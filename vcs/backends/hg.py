#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2010 Marcin Kuzminski,Lukasz Balcerzak.  All rights reserved.
#
"""
Created on Apr 8, 2010

:author: marcink,lukaszb
"""
import os
import datetime

from vcs.backends.base import BaseRepository, BaseChangeset
from vcs.exceptions import RepositoryError, VCSError, ChangesetError
from vcs.nodes import FileNode, DirNode, NodeKind, RootNode
from vcs.utils import abspath
from vcs.utils.lazy import LazyProperty

from mercurial import ui
from mercurial.localrepo import localrepository
from mercurial.error import RepoError
from mercurial.hgweb.hgwebdir_mod import findrepos

def get_repositories(repos_prefix, repos_path, baseui):
    """
    Listing of repositories in given path. This path should not be a repository
    itself. Return a list of repository objects
    :param repos_path: path to directory it could take syntax with * or ** for
    deep recursive displaying repositories
    """
    if not repos_path.endswith('*') and not repos_path.endswith('*'):
        raise VCSError('You need to specify * or ** at the end of path \
        for recursive scanning')

    check_repo_dir(repos_path)
    repos = findrepos([(repos_prefix, repos_path)])

    if not isinstance(baseui, ui.ui):
        baseui = ui.ui()

    my_ui = ui.ui()
    my_ui.setconfig('ui', 'report_untrusted', 'off')
    my_ui.setconfig('ui', 'interactive', 'off')

    repos_list = []
    for name, path in repos:
        try:
            r = MercurialRepository(path, baseui=baseui)
            repos_list.append(r)
        except OSError:
            continue
    return repos_list


def check_repo_dir(path):
    """
    Checks the repository
    :param path:
    """
    repos_path = path.split('/')
    if repos_path[-1] in ['*', '**']:
        repos_path = repos_path[:-1]
    if repos_path[0] != '/':
        repos_path[0] = '/'
    if not os.path.isdir(os.path.join(*repos_path)):
        raise RepositoryError('Not a valid repository in %s' % path[0][1])



class MercurialRepository(BaseRepository):
    """
    Mercurial repository backend
    """

    def __init__(self, repo_path, create=False, baseui=ui.ui()):
        """
        Raises RepositoryError if repository could not be find at the given
        ``repo_path``.

        :param repo_path: local path of the repository
        :param create=False: if set to True, would try to craete repository if
           it does not exist rather than raising exception
        :param baseui=mercurial.ui.ui(): user data
        """

        self.path = abspath(repo_path)
        self.baseui = baseui
        # We've set path and ui, now we can set repo itself
        self._set_repo(create)
        self.description = self.get_description()
        self.contact = self.get_contact()
        self.last_change = self.get_last_change()
        self.revisions = list(self.repo)
        self.changesets = {}

    @LazyProperty
    def name(self):
        return os.path.basename(self.path)

    @LazyProperty
    def branches(self):
        return self.repo.branchmap().keys()

    @LazyProperty
    def tags(self):
        return self.repo.tags().keys()

    def _set_repo(self, create):
        """
        Function will check for mercurial repository in given path and return
        a localrepo object. If there is no repository in that path it will raise
        an exception unless ``create`` parameter is set to True - in that case
        repository would be created and returned.
        """
        try:
            self.repo = localrepository(self.baseui, self.path, create=create)
        except RepoError, err:
            if create:
                msg = "Cannot create repository at %s. Original error was %s"\
                    % (self.path, err)
            else:
                msg = "Not valid repository at %s. Original error was %s"\
                    % (self.path, err)
            raise RepositoryError(msg)

    def get_description(self):
        undefined_description = 'unknown'
        return self.repo.ui.config('web', 'description',
                                   undefined_description, untrusted=True)

    def get_contact(self):
        from mercurial.hgweb.common import get_contact
        undefined_contact = 'Unknown'
        return get_contact(self.repo.ui.config) or undefined_contact

    def get_last_change(self):
        from mercurial.util import makedate
        return (self._get_mtime(self.repo.spath), makedate()[1])

    def _get_mtime(self, spath):
        cl_path = os.path.join(spath, "00changelog.i")
        if os.path.exists(cl_path):
            return os.stat(cl_path).st_mtime
        else:
            return os.stat(spath).st_mtime

    def _get_hidden(self):
        return self.repo.ui.configbool("web", "hidden", untrusted=True)

    def _get_revision(self, revision):
        if revision in (None, 'tip'):
            revision = self.revisions[-1]
        elif revision not in self.revisions:
            raise RepositoryError("Revision %r does not exist for this "
                "repository %s" % (revision, self))
        return revision

    def _get_archives(self):
        allowed = self.baseui.configlist("web", "allow_archive", untrusted=True)
        for i in [('zip', '.zip'), ('gz', '.tar.gz'), ('bz2', '.tar.bz2')]:
            if i[0] in allowed or self.repo.ui.configbool("web", "allow" + i[0],
                                                untrusted=True):
                yield {"type" : i[0], "extension": i[1], "node": 'tip'}

    def get_changeset(self, revision=None):
        """
        Returns ``MercurialChangeset`` object representing repository's
        changeset at the given ``revision``.
        """
        revision = self._get_revision(revision)
        if not self.changesets.has_key(revision):
            changeset = MercurialChangeset(repository=self, revision=revision)
            self.changesets[revision] = changeset
        return self.changesets[revision]

    def get_changesets(self, limit=10):
        """
        Return last n number of ``MercurialChangeset`` specified by limit
        attribute if None is given whole list of revisions is returned
        @param limit: int limit or None
        """
        limit = -limit if limit else None
        for i in reversed(self.revisions[limit:]):
            yield self.get_changeset(i)

class MercurialChangeset(BaseChangeset):
    """
    Represents state of the repository at the single revision.
    """

    def __init__(self, repository, revision):
        self.repository = repository
        self.revision = repository._get_revision(revision)
        ctx = repository.repo[revision]
        self._ctx = ctx
        self.author = ctx.user()
        self.message = ctx.description()
        self.branch = ctx.branch()
        self.tags = ctx.tags()
        self.date = datetime.datetime.fromtimestamp(ctx.date()[0])
        self._file_paths = list(ctx)
        self._dir_paths = list(set(map(os.path.dirname, self._file_paths)))
        self._paths = self._dir_paths + self._file_paths
        self.nodes = {}

    @LazyProperty
    def _paths(self):
        return self._dir_paths + self._file_paths

    def _fix_path(self, path):
        """
        Paths are stored without trailing slash so we need to get rid off it if
        needed.
        """
        if path.endswith('/'):
            path = path.rstrip('/')
        return path

    def _get_kind(self, path):
        path = self._fix_path(path)
        if path in self._file_paths:
            return NodeKind.FILE
        elif path in self._dir_paths:
            return NodeKind.DIR
        else:
            raise ChangesetError("Node does not exist at the given path %r"
                % (path))

    def get_file_content(self, path):
        """
        Returns content of the file at given ``path``.
        """
        if self._get_kind(path) != NodeKind.FILE:
            raise ChangesetError("File does not exist for revision %r at "
                " %r" % (self.revision, path))
        fctx = self._ctx[path]
        return fctx.data()

    def get_nodes(self, path):
        """
        Returns combined ``DirNode`` and ``FileNode`` objects list representing
        state of changeset at the given ``path``. If node at the given ``path``
        is not instance of ``DirNode``, ChangesetError would be raised.
        """

        if self._get_kind(path) != NodeKind.DIR:
            raise ChangesetError("Directory does not exist for revision %r at "
                " %r" % (self.revision, path))
        path = self._fix_path(path)
        filenodes = [FileNode(f, changeset=self) for f in self._file_paths
            if os.path.dirname(f) == path]
        dirs = set((path for path in map(os.path.dirname, self._file_paths)
            if path))
        dirnodes = [DirNode(d, changeset=self) for d in dirs
            if os.path.dirname(d) == path]
        nodes = dirnodes + filenodes
        # cache nodes
        for node in nodes:
            self.nodes[node.path] = node
        nodes.sort()
        return nodes

    def get_node(self, path):
        """
        Returns ``Node`` object from the given ``path``. If there is no node at
        the given ``path``, ``ChangesetError`` would be raised.
        """

        path = self._fix_path(path)
        if not path in self.nodes:
            if path in self._file_paths:
                node = FileNode(path, changeset=self)
            elif path in self._dir_paths or path in self._dir_paths:
                if path == '':
                    node = RootNode(changeset=self)
                else:
                    node = DirNode(path, changeset=self)
            else:
                raise ChangesetError("There is no file nor directory "
                    "at the given path: %r" % path)
            # cache node
            self.nodes[path] = node
        return self.nodes[path]


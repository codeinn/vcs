#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2010 Marcin Kuzminski,Lukasz Balcerzak.  All rights reserved.
#
"""
Created on Apr 8, 2010

@author: marcink,lukaszb
"""
import os
import datetime

from vcs.backends.base import BaseRepository, BaseChangeset
from vcs.exceptions import RepositoryError, VCSError, ChangesetError
from vcs.nodes import FileNode, DirNode, NodeKind

from mercurial import ui
from mercurial.localrepo import localrepository
from mercurial.error import RepoError
from mercurial.hgweb.hgwebdir_mod import findrepos

def get_repositories(repos_prefix, repos_path, baseui):
    """
    Listing of repositories in given path. This path should not be a repository
    itself. Return a list of repository objects
    @param repos_path: path to directory it could take syntax with * or ** for
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
            r = MercurialRepository(path, baseui)
            repos_list.append(r)
        except OSError:
            continue
    return repos_list


def check_repo_dir(path):
    """
    Checks the repository
    @param path:
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

    def __init__(self, repo_path, baseui=None):
        """
        Constructor
        """
        #self.repo = self._is_mercurial_repo(repo_path)
        self.path = repo_path
        self.baseui = baseui
        self.repo = self.init()
        self.name = self.get_name()
        self.description = self.get_description()
        self.contact = self.get_contact()
        self.last_change = self.get_last_change()
        self.revisions = list(self.repo)
        self.changesets = {}

    def _is_mercurial_repo(self, path):
        """
        Function will check for mercurial repository in given path and return
        a localrepo object. If there is no repository in that path it will raise
        an exception
        @param path:
        """
        path = path.replace('*', '')
        try:
            return  localrepository(ui.ui(), path)
        except (RepoError):
            raise RepositoryError('Not a valid repository in %s' % path)

    def init(self):
        """
        Initializes repository.
        """
        try:
            repo = localrepository(ui.ui(), self.path, create=True)
        except RepoError:
            repo = localrepository(ui.ui(), self.path)
        return repo

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

    def _get_archive_list(self):
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
        attribute
        @param limit:
        """
        for i in reversed(self.revisions[-limit:]):
            yield self.get_changeset(i)

    def get_name(self):
        return self.repo.path.split('/')[-2]

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
        self.date = datetime.datetime.fromtimestamp(sum(ctx.date()))
        self._file_paths = list(ctx)
        self._dir_paths = list(set(map(os.path.dirname, self._file_paths)))
        self.nodes = {}

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

    def _get_file_content(self, path):
        """
        Returns content of the file at given ``path``.
        """
        if self._get_kind(path) != NodeKind.FILE:
            raise ChangesetError("File does not exist for revision %r at "
                " %r" % (self.revision, path))
        fctx = self._ctx[path]
        return fctx.data()

    def _get_dir_nodes(self, path):
        """
        Returns combined file and dir nodes for a DirNode at the given ``path``.
        """
        if self._get_kind(path) != NodeKind.DIR:
            raise ChangesetError("Directory does not exist for revision %r at "
                " %r" % (self.revision, path))
        path = self._fix_path(path)
        filenodes = [FileNode(f, content=None) for f in self._file_paths
            if os.path.dirname(f) == path]
        dirs = set(map(os.path.dirname, self._file_paths))
        dirnodes = [DirNode(d, nodes=[]) for d in dirs
            if os.path.dirname(d) == path]
        nodes = dirnodes + filenodes
        nodes.sort()
        return nodes

    def get_node(self, path):
        path = self._fix_path(path)
        if not path in self.nodes:
            if path in self._file_paths:
                content = self._get_file_content(path)
                node = FileNode(path, content=content)
            elif path in self._dir_paths or path in self._dir_paths:
                nodes = self._get_dir_nodes(path)
                node = DirNode(path, nodes=nodes)
            else:
                raise ChangesetError("There is no file nor directory "
                    "at the given path: %r" % path)
            self.nodes[path] = node
        return self.nodes[path]


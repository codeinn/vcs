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
from vcs.nodes import Node, FileNode, DirNode, NodeKind
from vcs.utils.lazy import LazyProperty

from mercurial import ui
from mercurial.localrepo import localrepository
from mercurial import hg
from mercurial.error import RepoError
from mercurial.hgweb.hgwebdir_mod import findrepos

def get_repositories(repos_prefix, repos_path):
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
    if is_mercurial_repo(repos_path):
        pass
    repos = findrepos([(repos_prefix, repos_path)])

    my_ui = ui.ui()
    my_ui.setconfig('ui', 'report_untrusted', 'off')
    my_ui.setconfig('ui', 'interactive', 'off')

    repos_dict = {}
    for name, path in repos:
        u = my_ui.copy()

        try:
            u.readconfig(os.path.join(path, '.hg', 'hgrc'))
        except Exception, e:
            u.warn('error reading %s/.hg/hgrc: %s\n') % (path, e)
            continue

        #skip hidden repo
        if u.configbool("web", "hidden", untrusted=True):
            continue

        #skip not allowed
#       if not self.read_allowed(u, req):
#           continue

        try:
            r = localrepository(my_ui, path)
            repos_dict[name] = r
        except OSError:
            continue
    return repos_dict

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

def is_mercurial_repo(path):
    path = path.replace('*', '')
    try:
        hg.repository(ui.ui(), path)
        return True
    except (RepoError):
        return False

class MercurialRepository(BaseRepository):
    """
    Mercurial repository backend
    """

    def __init__(self, repo_path, **kwargs):
        """
        Constructor
        """
        baseui = ui.ui()
        self.repo = localrepository(baseui, path=repo_path)
        self.revisions = list(self.repo)
        self.changesets = {}

    def _get_revision(self, revision):
        if revision in (None, 'tip'):
            revision = self.revisions[-1]
        return revision

    def get_changeset(self, revision=None):
        """
        Returns ``MercurialChangeset`` object representing repository's
        changeset at the given ``revision``.
        """
        if not self.changesets.has_key(revision):
            changeset = MercurialChangeset(repository=self, revision=revision)
            self.changesets[revision] = changeset
        return self.changesets[revision]

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

    def get_node(self, path):
        if not path in self.nodes:
            if path in self._file_paths:
                content = self.get_file_content(path)
                node = FileNode(path, content=content)
            else:
                # paths are stored without trailing slash so we need to get
                # rid off it if needed
                if path.endswith('/'):
                    path = path.rstrip('/')
                if path in self._dir_paths or path in self._dir_paths:
                    node = DirNode(path)
                else:
                    raise ChangesetError("There is no file nor directory "
                        "at the given path: %r" % path)
            self.nodes[path] = node
        return self.nodes[path]

    def get_file_content(self, path):
        fctx = self._ctx[path]
        return fctx.data()


#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2010 Marcin Kuzminski,Lukasz Balcerzak.  All rights reserved.
#
"""
Created on May 21, 2010

:author: marcink,lukaszb
"""

import os
import re
import datetime
import time

from subprocess import Popen, PIPE

from itertools import chain

from vcs.backends.base import BaseRepository, BaseChangeset
from vcs.exceptions import RepositoryError, ChangesetError
from vcs.nodes import FileNode, DirNode, NodeKind, RootNode, RemovedFileNode
from vcs.utils.paths import abspath
from vcs.utils.lazy import LazyProperty

from dulwich.repo import Repo, NotGitRepository
from dulwich import objects

class GitRepository(BaseRepository):
    """
    Git repository backend
    """

    def __init__(self, repo_path, create=False):

        self.path = abspath(repo_path)
        self.changesets = {}
        self._set_repo(create)
        try:
            self.head = self._repo.head()
        except KeyError:
            self.head = None
        self.revisions = self._get_all_revisions()
        self.changesets = {}

    def run_git_command(self, cmd):
        """
        Runs given ``cmd`` as git command and returns tuple
        (returncode, stdout, stderr).

        .. note::
           This method exists only until log/blame functionality is implemented
           at Dulwich (see https://bugs.launchpad.net/bugs/645142). Parsing
           os command's output is road to hell...

        :param cmd: git command
        :param repo_path: if given, command would prefixed with
          --git-dir=repo_path/.git (note that ".git" is always appended
        """
        cmd = '--git-dir=%s %s' % (os.path.join(self.path, '.git'), cmd)
        try:
            p = Popen('git %s' % cmd, shell=True, stdout=PIPE, stderr=PIPE)
        except OSError, err:
            raise RepositoryError("Couldn't run git command (%s).\n"
                "Original error was:%s" % (cmd, err))
        so, se = p.communicate()
        if not se.startswith("fatal: bad default revision 'HEAD'") and \
            p.returncode != 0:
            raise RepositoryError("Couldn't run git command (%s).\n"
                "stderr:\n%s" % (cmd, se))
        return so, se

    def _set_repo(self, create):
        if create and os.path.exists(self.path):
            raise RepositoryError("Location already exist")
        try:
            if create:
                os.mkdir(self.path)
                self._repo = Repo.init(self.path)
            else:
                self._repo = Repo(self.path)
        except (NotGitRepository, OSError), err:
            raise RepositoryError(str(err))

    def _get_all_revisions(self):
        cmd = 'log --pretty=oneline'
        so, se = self.run_git_command(cmd)
        revisions = [line.split()[0] for line in so.split('\n')[:-1]]
        revisions.reverse()
        return revisions

    def _get_revision(self, revision):
        if len(self.revisions) == 0:
            raise RepositoryError("There are no changesets yet")
        if revision in (None, 'tip', 'HEAD', 'head', -1):
            return self.revisions[-1]
        if isinstance(revision, (str, unicode)):
            pattern = re.compile(r'^[[0-9a-fA-F]{12}|[0-9a-fA-F]{40}]$')
            if not pattern.match(revision):
                raise RepositoryError("Revision %r does not exist for this "
                    "repository %s" % (revision, self))
            return revision
        raise RepositoryError("Given revision %r not recognized" % revision)

    def _get_tree(self, id):
        return self._repo[id]

    @LazyProperty
    def name(self):
        return os.path.basename(self.path)

    @LazyProperty
    def last_change(self):
        """
        Returns last change made on this repository
        """
        from vcs.utils import makedate
        return (self._get_mtime(), makedate()[1])

    def _get_mtime(self):
        try:
            return time.mktime(self.get_changeset().date.timetuple())
        except RepositoryError:
            #fallback to filesystem
            in_path = os.path.join(self.path, '.git', "index")
            he_path = os.path.join(self.path, '.git', "HEAD")
            if os.path.exists(in_path):
                return os.stat(in_path).st_mtime
            else:
                return os.stat(he_path).st_mtime

    @LazyProperty
    def description(self):
        undefined_description = 'unknown'
        description_path = os.path.join(self.path, '.git', 'description')
        if os.path.isfile(description_path):
            return open(description_path).read()
        else:
            return undefined_description

    @LazyProperty
    def branches(self):
        if not self.revisions:
            return {}
        return dict((ref.split('/')[-1], id)
            for ref, id in self._repo.get_refs().items()
            if ref.startswith('refs/remotes/') and not ref.endswith('/HEAD'))

    @LazyProperty
    def tags(self):
        if not self.revisions:
            return {}
        return dict((ref.split('/')[-1], id) for ref, id in
            self._repo.get_refs().items()
            if ref.startswith('refs/tags/'))

    def get_changeset(self, revision=None):
        """
        Returns ``GitChangeset`` object representing commit from git repository
        at the given revision or head (most recent commit) if None given.
        """
        revision = self._get_revision(revision)
        if not self.changesets.has_key(revision):
            changeset = GitChangeset(repository=self, revision=revision)
            self.changesets[changeset.revision] = changeset
        return self.changesets[revision]

    def get_changesets(self, limit=10, offset=None):
        """
        Return last n number of ``MercurialChangeset`` specified by limit
        attribute if None is given whole list of revisions is returned
        :param limit: int limit or None
        """
        count = self.count()
        offset = offset or 0
        limit = limit or None
        i = 0
        while True:
            if limit and i == limit:
                break
            i += 1
            rev_index = count - offset - i
            if rev_index < 0:
                break
            id = self.revisions[rev_index]
            yield self.get_changeset(id)

class GitChangeset(BaseChangeset):
    """
    Represents state of the repository at single revision.
    """

    def __init__(self, repository, revision):
        self.repository = repository
        self.revision = repository._get_revision(revision)
        try:
            commit = self.repository._repo.get_object(revision)
        except KeyError:
            raise RepositoryError("Cannot get object with id %s" % revision)
        self._commit = commit
        self._tree_id = commit.tree
        self.author = unicode(commit.committer)
        try:
            self.message = unicode(commit.message[:-1]) # Always strip last eol
        except UnicodeDecodeError:
            self.message = commit.message[:-1].decode(commit.encoding
                or 'utf-8')
        #self.branch = None
        #self.tags =
        self.date = datetime.datetime.fromtimestamp(commit.commit_time)
        #tree = self.repository.get_object(self._tree_id)
        self.nodes = {}
        self.id = revision
        self.raw_id = revision
        self._paths = {}

    @LazyProperty
    def branch(self):
        # TODO: Cache as we walk (id <-> branch name mapping)
        refs = self.repository._repo.get_refs()
        heads = [(key[len('refs/heads/'):], val) for key, val in refs.items()
            if key.startswith('refs/heads/')]
        import pdb; pdb.set_trace()
        for name, id in heads:
            walker = self.repository._repo.object_store.get_graph_walker([id])
            while True:
                id = walker.next()
                if not id:
                    break
                if id == self.id:
                    return name
        raise ChangesetError("This should not happen... Have you manually "
            "change id of the changeset?")

    def _fix_path(self, path):
        """
        Paths are stored without trailing slash so we need to get rid off it if
        needed.
        """
        if path.endswith('/'):
            path = path.rstrip('/')
        return path

    def _get_id_for_path(self, path):
        if not path in self._paths:
            path = path.strip('/')
            # set root tree
            tree = self.repository._repo[self._commit.tree]
            if path == '':
                self._paths[''] = tree.id
                return tree.id
            splitted = path.split('/')
            dirs, name = splitted[:-1], splitted[-1]
            curdir = ''
            for dir in dirs:
                if curdir:
                    curdir = '/'.join((curdir, dir))
                else:
                    curdir = dir
                if curdir in self._paths:
                    # This path have been already traversed
                    # Update tree and continue
                    tree = self.repository._repo[self._paths[curdir]]
                    continue
                dir_id = None
                for item, stat, id in tree.iteritems():
                    if curdir:
                        item_path = '/'.join((curdir, item))
                    else:
                        item_path = item
                    self._paths[item_path] = id
                    if dir == item:
                        dir_id = id
                if dir_id:
                    # Update tree
                    tree = self.repository._repo[dir_id]
                    if not isinstance(tree, objects.Tree):
                        raise ChangesetError('%s is not a directory' % curdir)
                else:
                    raise ChangesetError('%s have not been found' % curdir)
            for item, stat, id in tree.iteritems():
                if curdir:
                    name = '/'.join((curdir, item))
                else:
                    name = item
                self._paths[name] = id
            if not path in self._paths:
                raise ChangesetError("There is no file nor directory "
                    "at the given path %r at revision %r"
                    % (path, self.revision))
        return self._paths[path]

    def _get_kind(self, path):
        id = self._get_id_for_path(path)
        obj = self.repository._repo[id]
        if isinstance(obj, objects.Blob):
            return NodeKind.FILE
        elif isinstance(obj, objects.Tree):
            return NodeKind.DIR

    def _get_file_nodes(self):
        return chain(*(t[2] for t in self.walk()))

    @LazyProperty
    def parents(self):
        """
        Returns list of parents changesets.
        """
        return [self.repository.get_changeset(parent)
            for parent in self._commit.parents]

    def get_file_content(self, path):
        """
        Returns content of the file at given ``path``.
        """
        id = self._get_id_for_path(path)
        blob = self.repository._repo[id]
        return blob.as_pretty_string()

    def get_file_size(self, path):
        """
        Returns size of the file at given ``path``.
        """
        id = self._get_id_for_path(path)
        blob = self.repository._repo[id]
        return blob.raw_length()

    def get_file_changeset(self, path):
        """
        Returns last commit of the file at the given ``path``.
        """
        node = self.get_node(path)
        return node.history[0]

    def get_file_history(self, path):
        """
        Returns history of file as reversed list of ``Changeset`` objects for
        which file at given ``path`` has been modified.

        TODO: This function now uses os underlying 'git' and 'grep' commands
        which is generally not good. Should be replaced with algorithm
        iterating commits.
        """
        cmd = 'log --name-status -p %s -- %s | grep "^commit"' % (self.id, path)
        so, se = self.repository.run_git_command(cmd)
        ids = re.findall(r'\w{40}', so)
        return [self.repository.get_changeset(id) for id in ids]

    def get_file_annotate(self, path):
        """
        Returns a list of three element tuples with lineno,changeset and line

        TODO: This function now uses os underlying 'git' command which is
        generally not good. Should be replaced with algorithm iterating
        commits.
        """
        cmd = 'blame %s -l --root -r %s' % (path, self.id)
        # -l     ==> outputs long shas (and we need all 40 characters)
        # --root ==> doesn't put '^' character for bounderies
        # -r sha ==> blames for the given revision
        so, se = self.repository.run_git_command(cmd)
        annotate = []
        for i, blame_line in enumerate(so.split('\n')[:-1]):
            ln_no = i + 1
            id, line = re.split(r' \(.+?\) ', blame_line)
            annotate.append((ln_no, self.repository.get_changeset(id), line))
        return annotate

    def get_nodes(self, path):
        if self._get_kind(path) != NodeKind.DIR:
            raise ChangesetError("Directory does not exist for revision %r at "
                " %r" % (self.revision, path))
        path = self._fix_path(path)
        id = self._get_id_for_path(path)
        tree = self.repository._repo[id]
        dirnodes = []
        filenodes = []
        for stat, name, id in tree.entries():
            obj = self.repository._repo.get_object(id)
            if path != '':
                obj_path = '/'.join((path, name))
            else:
                obj_path = name
            if isinstance(obj, objects.Tree):
                dirnodes.append(DirNode(obj_path, changeset=self))
            elif isinstance(obj, objects.Blob):
                filenodes.append(FileNode(obj_path, changeset=self))
            else:
                raise ChangesetError("Requested object should be Tree or Blob, "
                    "is %r" % type(obj))
        nodes = dirnodes + filenodes
        for node in nodes:
            if not node.path in self.nodes:
                self.nodes[node.path] = node
        nodes.sort()
        return nodes

    def get_node(self, path):
        path = self._fix_path(path)
        if not path in self.nodes:
            id = self._get_id_for_path(path)
            obj = self.repository._repo.get_object(id)
            if isinstance(obj, objects.Tree):
                if path == '':
                    node = RootNode(changeset=self)
                else:
                    node = DirNode(path, changeset=self)
            elif isinstance(obj, objects.Blob):
                node = FileNode(path, changeset=self)
            else:
                raise ChangesetError("There is no file nor directory "
                    "at the given path %r at revision %r"
                    % (path, self.revision))
            # cache node
            self.nodes[path] = node
        return self.nodes[path]

    @LazyProperty
    def added(self):
        """
        Returns list of added ``FileNode`` objects.
        """
        if not self.parents:
            return list(self._get_file_nodes())
        added_nodes = []
        old_files = set()
        for parent in self.parents:
            for f in parent._get_file_nodes():
                old_files.add(f.path)

        files = set([f.path for f in self._get_file_nodes()])
        for path in (files - old_files):
            added_nodes.append(self.get_node(path))

        return added_nodes

    @LazyProperty
    def changed(self):
        """
        Returns list of modified ``FileNode`` objects.
        """
        if not self.parents:
            return []
        changed_nodes = []
        not_changed_paths = [f.path for f in self.added + self.removed]
        for parent in self.parents:
            try:
                cmd = 'diff --stat %s %s' % (self.raw_id, parent.raw_id)
                so, se = self.repository.run_git_command(cmd)
                for line in so.split('\n')[:-2]:
                    path = line.split()[0]
                    if path in not_changed_paths:
                        continue
                    node = self.get_node(path)
                    changed_nodes.append(node)
            except ChangesetError:
                # If node cannot be found, just continue
                pass
        return changed_nodes

    @LazyProperty
    def removed(self):
        """
        Returns list of removed ``FileNode`` objects.
        """
        if not self.parents:
            return []
        removed_nodes = []
        old_files = set()
        for parent in self.parents:
            for f in parent._get_file_nodes():
                old_files.add(f.path)

        files = set([f.path for f in self._get_file_nodes()])
        for path in (old_files - files):
            node = RemovedFileNode(path)
            removed_nodes.append(node)

        return removed_nodes


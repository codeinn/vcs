#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2010 Marcin Kuzminski,Lukasz Balcerzak.  All rights reserved.
#
"""
Git backend implementation.
"""
import os
import re
import time

from subprocess import Popen, PIPE

from itertools import chain

from vcs.backends.base import BaseRepository
from vcs.backends.base import BaseChangeset
from vcs.backends.base import BaseInMemoryChangeset
from vcs.exceptions import RepositoryError
from vcs.exceptions import EmptyRepositoryError
from vcs.exceptions import ChangesetError
from vcs.exceptions import ChangesetDoesNotExistError
from vcs.exceptions import NodeDoesNotExistError
from vcs.nodes import FileNode, DirNode, NodeKind, RootNode, RemovedFileNode
from vcs.utils.paths import abspath
from vcs.utils.lazy import LazyProperty
from vcs.utils.ordered_dict import OrderedDict
from vcs.utils import safe_unicode, makedate, date_fromtimestamp

from dulwich.repo import Repo, NotGitRepository
from dulwich import objects

class GitRepository(BaseRepository):
    """
    Git repository backend.
    """

    def __init__(self, repo_path, create=False, src_url=None,
                 update_after_clone=False):

        self.path = abspath(repo_path)
        self.changesets = {}
        self._set_repo(create, src_url, update_after_clone)
        try:
            self.head = self._repo.head()
        except KeyError:
            self.head = None
        self.changesets = {}

    @LazyProperty
    def revisions(self):
        """
        Returns list of revisions' ids, in ascending order.  Being lazy
        attribute allows external tools to inject shas from cache.
        """
        return self._get_all_revisions()

    def run_git_command(self, cmd):
        """
        Runs given ``cmd`` as git command and returns tuple
        (returncode, stdout, stderr).

        .. note::
           This method exists only until log/blame functionality is implemented
           at Dulwich (see https://bugs.launchpad.net/bugs/645142). Parsing
           os command's output is road to hell...

        :param cmd: git command to be executed
        """
        #cmd = '(cd %s && git %s)' % (self.path, cmd)
        cmd = 'git %s' % cmd
        try:
            opts = dict(
                shell=True,
                stdout=PIPE,
                stderr=PIPE)
            if os.path.isdir(self.path):
                opts['cwd'] = self.path
            p = Popen(cmd, **opts)
        except OSError, err:
            raise RepositoryError("Couldn't run git command (%s).\n"
                "Original error was:%s" % (cmd, err))
        so, se = p.communicate()
        if not se.startswith("fatal: bad default revision 'HEAD'") and \
            p.returncode != 0:
            raise RepositoryError("Couldn't run git command (%s).\n"
                "stderr:\n%s" % (cmd, se))
        return so, se

    def _set_repo(self, create, src_url=None, update_after_clone=False):
        if create and os.path.exists(self.path):
            raise RepositoryError("Location already exist")
        if src_url and not create:
            raise RepositoryError("Create should be set to True if src_url is "
                                  "given (clone operation creates repository)")
        try:
            if create and src_url:
                self.clone(src_url, update_after_clone)
                self._repo = Repo(self.path)
            elif create:
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
        """
        For git backend we always return integer here. This way we ensure
        that changset's revision attribute would become integer.
        """
        if len(self.revisions) == 0:
            raise EmptyRepositoryError("There are no changesets yet")
        if revision in (None, 'tip', 'HEAD', 'head', -1):
            #return self.revisions[-1]
            revision = len(self.revisions) - 1
        if isinstance(revision, (str, unicode)) and revision.isdigit() \
            and len(revision) < 12:
            revision = int(revision)
        if isinstance(revision, int) and (
            revision < 0 or revision >= len(self.revisions)):
                raise ChangesetDoesNotExistError("Revision %r does not exist "
                    "for this repository %s" % (revision, self))
        elif isinstance(revision, (str, unicode)):
            pattern = re.compile(r'^[[0-9a-fA-F]{12}|[0-9a-fA-F]{40}]$')
            if not pattern.match(revision):
                raise ChangesetDoesNotExistError("Revision %r does not exist "
                    "for this repository %s" % (revision, self))
            try:
                revision = self.revisions.index(revision)
            except ValueError:
                raise ChangesetDoesNotExistError("Revision %r does not exist "
                    "for this repository %s" % (revision, self))
        # Ensure we return integer
        if not isinstance(revision, int):
            raise ChangesetDoesNotExistError("Given revision %r not recognized"
                % revision)
        return revision

    def _get_archives(self, archive_name='tip'):

        for i in [('zip', '.zip'), ('gz', '.tar.gz'), ('bz2', '.tar.bz2')]:
                yield {"type" : i[0], "extension": i[1], "node": archive_name}

    def _get_tree(self, id):
        return self._repo[id]

    def _get_url(self, url):
        """
        Returns normalized url. If schema is not given, would fall to filesystem
        (``file://``) schema.
        """
        url = str(url)
        if url != 'default' and not '://' in url:
            url = '://'.join(('file', url))
        return url

    @LazyProperty
    def name(self):
        return os.path.basename(self.path)

    @LazyProperty
    def last_change(self):
        """
        Returns last change made on this repository as datetime object
        """
        return date_fromtimestamp(self._get_mtime(), makedate()[1])

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
    def contact(self):
        undefined_contact = 'Unknown'
        return undefined_contact

    @LazyProperty
    def branches(self):
        if not self.revisions:
            return {}
        refs = self._repo.refs.as_dict()
        sortkey = lambda ctx:ctx[0]
        _branches = [(ref.split('/')[-1], head)
            for ref, head in refs.items()
            if ref.startswith('refs/heads/') or
            ref.startswith('refs/remotes/') and not ref.endswith('/HEAD')]
        return OrderedDict(sorted(_branches, key=sortkey, reverse=False))

    @LazyProperty
    def tags(self):
        if not self.revisions:
            return {}
        sortkey = lambda ctx:ctx[0]
        _tags = [(ref.split('/')[-1], head,) for ref, head in
            self._repo.get_refs().items() if ref.startswith('refs/tags/')]
        return OrderedDict(sorted(_tags, key=sortkey, reverse=True))

    def get_changeset(self, revision=None):
        """
        Returns ``GitChangeset`` object representing commit from git repository
        at the given revision or head (most recent commit) if None given.
        """
        revision = self._get_revision(revision)
        if not self.changesets.has_key(revision):
            changeset = GitChangeset(repository=self, revision=revision)
            self.changesets[changeset.revision] = changeset
            self.changesets[changeset.raw_id] = changeset
            self.changesets[changeset.short_id] = changeset
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

    @LazyProperty
    def in_memory_changeset(self):
        """
        Returns ``GitInMemoryChangeset`` object for this repository.
        """
        return GitInMemoryChangeset(self)

    def clone(self, url, update_after_clone):
        """
        Tries to clone changes from external location.
        if update_after_clone is set To false it'll prevent the runing update
        on workdir
        """
        url = self._get_url(url)
        cmd = 'clone '
        if not update_after_clone:
            cmd += '--no-checkout '
        cmd += '-- "%s" "%s"' % (url, self.path)
        # If error occurs run_git_command raises RepositoryError already
        self.run_git_command(cmd)


class GitChangeset(BaseChangeset):
    """
    Represents state of the repository at single revision.
    """

    def __init__(self, repository, revision):
        self.repository = repository
        self.revision = repository._get_revision(revision)
        self.raw_id = self.repository.revisions[revision]
        self.short_id = self.raw_id[:12]
        self.id = self.raw_id
        try:
            commit = self.repository._repo.get_object(self.raw_id)
        except KeyError:
            raise RepositoryError("Cannot get object with id %s" % self.raw_id)
        self._commit = commit
        self._tree_id = commit.tree
        self.author = safe_unicode(commit.committer)
        try:
            self.message = safe_unicode(commit.message[:-1]) # Always strip last eol
        except UnicodeDecodeError:
            self.message = commit.message[:-1].decode(commit.encoding
                or 'utf-8')
        self.branch = None
        self.tags = []
        self.date = date_fromtimestamp(commit.commit_time, commit.commit_timezone)
        #tree = self.repository.get_object(self._tree_id)
        self.nodes = {}
        self._paths = {}

    @LazyProperty
    def branch(self):
        # TODO: Cache as we walk (id <-> branch name mapping)
        refs = self.repository._repo.get_refs()
        heads = [(key[len('refs/heads/'):], val) for key, val in refs.items()
            if key.startswith('refs/heads/')]

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
                raise NodeDoesNotExistError("There is no file nor directory "
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
        cmd = 'log --name-status -p %s -- "%s" | grep "^commit"' % (self.id, path)
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
        cmd = 'blame -l --root -r %s -- "%s"' % (self.id, path)
        # -l     ==> outputs long shas (and we need all 40 characters)
        # --root ==> doesn't put '^' character for bounderies
        # -r sha ==> blames for the given revision
        so, se = self.repository.run_git_command(cmd)
        annotate = []
        for i, blame_line in enumerate(so.split('\n')[:-1]):
            ln_no = i + 1
            id, line = re.split(r' \(.+?\) ', blame_line, 1)
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
                raise NodeDoesNotExistError("There is no file nor directory "
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


class GitInMemoryChangeset(BaseInMemoryChangeset):

    def commit(self, message, author, **kwargs):
        """
        Performs in-memory commit.
        """

        repo = self.repository._repo
        object_store = repo.object_store
        try:
            tip = self.repository.get_changeset()
        except RepositoryError:
            tip = None

        ENCODING = "UTF-8"

        # Create tree and populates it with blobs
        tree = tip and repo[tip._commit.tree] or objects.Tree()
        for node in self.added:
            blob = objects.Blob.from_string(node.content.encode(ENCODING))
            tree.add(0100644, node.path, blob.id)
            object_store.add_object(blob)
        for node in self.changed:
            blob = objects.Blob.from_string(node.content.encode(ENCODING))
            tree[node.path] = 0100644, blob.id
            object_store.add_object(blob)
        for node in self.removed:
            del tree[node.path]
        object_store.add_object(tree)

        # Create commit
        commit = objects.Commit()
        commit.tree = tree.id
        commit.parents = tip and [tip.id] or []
        commit.author = commit.committer = author
        commit.commit_time = commit.author_time = int(time.time())
        tz = time.timezone
        commit.commit_timezone = commit.author_timezone = tz
        commit.encoding = ENCODING
        commit.message = message + ' '

        object_store.add_object(commit)

        ref = 'refs/heads/master'
        repo.refs[ref] = commit.id
        repo.refs['HEAD'] = commit.id

        # Update vcs repository object & recreate dulwich repo
        self.repository.revisions.append(commit.id)
        self.repository._repo = Repo(self.repository.path)
        self.repository.changesets.pop(None, None)
        tip = self.repository.get_changeset()
        self.reset()
        return tip


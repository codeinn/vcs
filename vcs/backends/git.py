import os
import re
import datetime
import warnings

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

        warnings.warn("Git backend is only a proof by now")

        self.path = abspath(repo_path)
        self.changesets = {}
        self._set_repo(create)
        self.head = self._repo.head()
        self.revisions = [commit.id for commit in
            reversed(self._repo.revision_history(self.head))]
        self.changesets = {}

    def _set_repo(self, create):
        try:
            self._repo = Repo(self.path)
        except NotGitRepository, err:
            raise RepositoryError(str(err))

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

    def _get_tree(self, hex):
        return self._repo.tree(hex)

    @LazyProperty
    def name(self):
        return os.path.basename(self.path)

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
        @param limit: int limit or None
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
            hex = self.revisions[rev_index]
            yield self.get_changeset(hex)

class GitChangeset(BaseChangeset):
    """
    Represents state of the repository at single revision.
    """

    def __init__(self, repository, revision):
        self.repository = repository
        self.revision = repository._get_revision(revision)
        commit = self.repository._repo.get_object(revision)
        self._commit = commit
        self._tree_id = commit.tree
        self.author = commit.committer
        self.message = commit.message
        #self.branch = None
        #self.tags =
        self.date = datetime.datetime.fromtimestamp(commit.commit_time)
        #tree = self.repository.get_object(self._tree_id)
        self.nodes = {}
        self.id = revision
        self.raw_id = revision
        self._paths = {}

    def _fix_path(self, path):
        """
        Paths are stored without trailing slash so we need to get rid off it if
        needed.
        """
        if path.endswith('/'):
            path = path.rstrip('/')
        return path

    def _get_hex_for_path(self, path):
        if not path in self._paths:
            tree = self.repository._repo[self._commit.tree]
            if path == '':
                self._paths[''] = tree.id
                return tree.id
            splitted = path.split('/')
            parent = None
            spath, basename = splitted[:-1], splitted[-1]
            parent = None
            # Walk through the path
            while spath:
                dir = spath.pop(0)
                for stat, name, hex in tree.entries():
                    if parent is None:
                        # Root directory
                        self._paths[name] = hex
                    else:
                        fullpath = '/'.join((parent, name))
                        self._paths[fullpath] = hex
                    if dir == name:
                        tree = self.repository._repo.tree(hex)
                if parent:
                    parent = '/'.join((parent, dir))
                else:
                    parent = dir
            for stat, name, hex in tree.entries():
                if parent is None:
                    self._paths[name] = hex
                else:
                    fullpath = '/'.join((parent, name))
                    self._paths[fullpath] = hex
            if not path in self._paths:
                print self._paths
                raise ChangesetError("There is no file nor directory "
                    "at the given path %r at revision %r"
                    % (path, self.revision))
        return self._paths[path]

    def _get_kind(self, path):
        hex = self._get_hex_for_path(path)
        obj = self.repository._repo[hex]
        if isinstance(obj, objects.Blob):
            return NodeKind.FILE
        elif isinstance(obj, objects.Tree):
            return NodeKind.DIR

    def get_file_content(self, path):
        """
        Returns content of the file at given ``path``.
        """
        hex = self._get_hex_for_path(path)
        blob = self.repository._repo[hex]
        return blob.as_pretty_string()

    def get_file_size(self, path):
        """
        Returns size of the file at given ``path``.
        """
        hex = self._get_hex_for_path(path)
        blob = self.repository._repo[hex]
        return blob.raw_length()

    @LazyProperty
    def parents(self):
        """
        Returns list of parents changesets.
        """
        return [self.repository.get_changeset(parent)
            for parent in self._commit.parents]

    def get_nodes(self, path):
        if self._get_kind(path) != NodeKind.DIR:
            raise ChangesetError("Directory does not exist for revision %r at "
                " %r" % (self.revision, path))
        path = self._fix_path(path)
        hex = self._get_hex_for_path(path)
        tree = self.repository._repo[hex]
        dirnodes = []
        filenodes = []
        for stat, name, hex in tree.entries():
            obj = self.repository._repo.get_object(hex)
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
            hex = self._get_hex_for_path(path)
            obj = self.repository._repo.get_object(hex)
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


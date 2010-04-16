"""

"""
import posixpath

from vcs.utils.lazy import LazyProperty
from vcs.exceptions import VCSError

class NodeError(VCSError):
    pass

class NodeKind:
    DIR = 1
    FILE = 2

class Node(object):
    """
    Simplest class representing file or directory on repository.  SCM backends
    should use ``FileNode`` and ``DirNode`` subclasses rather than ``Node``
    directly.

    Node's ``path`` cannot start with slash as we oparete on *relative* paths
    only. Moreover, every single node is identified by the ``path`` attribute,
    so it cannot end with slash, too. Otherwise, path could lead to mistakes.
    """

    def __init__(self, path, kind):
        if path.startswith('/'):
            raise NodeError("Cannot initialize Node objects with slash at "
                "the beginning as only relative paths are supported")
        self.path = path.rstrip('/')
        if path == '' and kind != NodeKind.DIR:
            raise NodeError("Only DirNode and its subclasses may be initialized"
                " with empty path")
        self.kind = kind
        self.dirs, self.files = [], []
        if self.is_root() and not self.is_dir():
            raise NodeError, "Root node cannot be FILE kind"

    @LazyProperty
    def parent(self):
        parent_path = self.get_parent_path()
        if parent_path:
            return Node(parent_path, NodeKind.DIR)
        return None

    @LazyProperty
    def name(self):
        """
        Returns name of the node so if its path
        then only last part is returned.
        """
        return self.path.rstrip('/').split('/')[-1]

    def _get_kind(self):
        return self._kind

    def _set_kind(self, kind):
        if hasattr(self, '_kind'):
            raise NodeError, "Cannot change node's kind"
        else:
            self._kind = kind
            # Post setter check (path's trailing slash)
            if self.path.endswith('/'):
                raise NodeError, "Node's path cannot end with slash"
            #elif not self.path=='' and self.is_dir() and \
            #        not self.path.endswith('/'):
            #    raise NodeError, "Dir nodes' paths must end with slash"

    kind = property(_get_kind, _set_kind)

    def __cmp__(self, other):
        """
        Comparator using name of the node, needed for quick list sorting.
        """
        kind_cmp = cmp(self.kind, other.kind)
        if kind_cmp:
            return kind_cmp
        return cmp(self.name, other.name)

    def __eq__(self, other):
        for attr in self.__dict__:
            if self.__dict__[attr] != other.__dict__[attr]:
                return False
        return True

    def __nq__(self, other):
        return not self == other

    def __repr__(self):
        return '<%s %r>' % (self.__class__.__name__, self.path)

    def __str__(self):
        return self.__repr__()

    def __unicode__(self):
        return unicode(self.name)

    def get_parent_path(self):
        """
        Returns node's parent path or empty string if node is root.
        """
        if self.is_root():
            return ''
        return posixpath.dirname(self.path.rstrip('/')) + '/'

    def is_file(self):
        """
        Returns ``True`` if node's kind is ``NodeKind.FILE``, ``False``
        otherwise.
        """
        return self.kind == NodeKind.FILE

    def is_dir(self):
        """
        Returns ``True`` if node's kind is ``NodeKind.DIR``, ``False``
        otherwise.
        """
        return self.kind == NodeKind.DIR

    def is_root(self):
        """
        Returns ``True`` if node is a root node and ``False`` otherwise.
        """
        return self.kind == NodeKind.DIR and self.path == ''

    def get_mimetype(self, content):
        # Use chardet/python-magic/mimetypes?
        raise NotImplementedError


class FileNode(Node):
    """
    Class representing file nodes.

    :attribute: path: path to the node, relative to repostiory's root
    :attribute: content: if given arbitrary sets content of the file
    :attribute: changeset: if given, first time content is accessed, callback
    """

    def __init__(self, path, content=None, changeset=None):
        """
        Only one of ``content`` and ``changeset`` may be given.
        function fetching content using changeset would be used

        :param path: relative path to the node
        :param content: content may be passed to constructor
        :param changeset: if given, will use it to lazily fetch content
        """

        if content and changeset:
            raise NodeError("Cannot set both content and changeset")
        super(FileNode, self).__init__(path, kind=NodeKind.FILE)
        self.changeset = changeset
        self._content = content

    @LazyProperty
    def content(self):
        if self.changeset:
            return self.changeset._get_file_content(self.path)
        else:
            return self._content

    @LazyProperty
    def nodes(self):
        raise NodeError("%s represents a file and has no ``nodes`` attribute"
            % self)

class DirNode(Node):
    """
    DirNode stores list of files and directories within this node.
    Nodes may be used standalone but within repository context they
    lazily fetch data within same repositorty's changeset.
    """

    def __init__(self, path, nodes=()):
        super(DirNode, self).__init__(path, NodeKind.DIR)
        self.nodes = nodes

    @LazyProperty
    def content(self):
        raise NodeError("%s represents a dir and has no ``content`` attribute"
            % self)

    def __iter__(self):
        for node in self.nodes:
            yield node

    def __getitem__(self, path):
        try:
            return self._nodes[path]
        except KeyError:
            raise NodeError("Node does not exist at %s" % path)

    def _get_nodes(self):
        """
        Returns combined files and dirs nodes within this dirnode.
        """
        return sorted(self._nodes.values())

    def _set_nodes(self, nodes):
        """
        Sets combined files and dirs for this dirnode. Backends should set this
        attribute.
        """
        if not self.is_dir():
            raise NodeError("Is not a dir!")

        self.files = sorted([node for node in nodes if node.is_file()])
        self.dirs = sorted([node for node in nodes if node.is_dir()])

        self._nodes = dict((node.path, node) for node in nodes)

    nodes = property(_get_nodes, _set_nodes)

class RootNode(DirNode):
    """
    DirNode being the root node of the repository.
    """

    def __init__(self, nodes=()):
        super(RootNode, self).__init__(path='', nodes=nodes)

    def __repr__(self):
        return '<%s>' % self.__class__.__name__


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
    Simplest class representing file or directory on repository.
    SCM backends should use ``FileNode`` and ``DirNode`` subclasses rather than
    ``Node`` directly.

    We assert that if node's kind is DIR then it's path **MUST** have trailing
    slash (with one exception: root nodes have kind DIR but root node's path is
    always empty string) and FILE node's path **CANNOT** end with slash.
    Moreover, node's path cannot start with slash, too, as we oparete on
    *relative* paths only (this class is out of any context).
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
        self.name = path.rstrip('/').split('/')[-1]
        self.dirs, self.files = [], []
        if self.is_root() and not self.is_dir():
            raise NodeError, "Root node cannot be FILE kind"

    @LazyProperty
    def parent(self):
        parent_path = self.get_parent_path()
        if parent_path:
            return Node(parent_path, NodeKind.DIR)
        return None

    def _get_kind(self):
        return self._kind

    def _set_kind(self, kind):
        if hasattr(self, '_kind'):
            raise NodeError, "Cannot change node's kind"
        else:
            self._kind = kind
            # Post setter check (path's trailing slash)
            if self.is_file() and self.path.endswith('/'):
                raise NodeError, "File nodes' paths cannot end with slash"
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
        return '<Node %r>' % self.path

    def __unicode__(self):
        return unicode(self.name)

    @staticmethod
    def get_name(path):
        """
        Returns name of the node so if its path
        then only last part is returned.
        """
        return path.split('/')[-1]

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
    """

    def __init__(self, path, content=None):
        super(FileNode, self).__init__(path, kind=NodeKind.FILE)
        self.content = content

    @LazyProperty
    def nodes(self):
        raise NodeError("%s represents a file and has no ``nodes`` attribute"
            % self)

    def __repr__(self):
        return '<FileNode %r>' % self.path

class DirNode(Node):
    """
    DirNode stores list of files and directories within this node.
    """

    def __init__(self, path, nodes=()):
        super(DirNode, self).__init__(path, NodeKind.DIR)
        self.nodes = nodes

    @LazyProperty
    def content(self):
        raise NodeError("%s represents a dir and has no ``content`` attribute"
            % self)

    def __repr__(self):
        return '<DirNode %r>' % self.path

    def get_nodes(self):
        """
        Returns combined files and dirs nodes within this dirnode.
        """
        return self._nodes

    def set_nodes(self, nodes):
        """
        Sets combined files and dirs for this dirnode. Backends should set this
        attribute.
        """
        if not self.is_dir():
            raise NodeError("Is not a dir!")

        self.files = [node for node in nodes if node.is_file()]
        self.dirs = [node for node in nodes if node.is_dir()]

        self._nodes = nodes

    nodes = property(get_nodes, set_nodes)

class RootNode(Node):
    """
    DirNode being the root node of the repository.
    """

    def __init__(self, nodes=()):
        super(DirNode, self).__init__(path='', kind=NodeKind.DIR)


"""

"""
import posixpath
import mimetypes

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
        #self.dirs, self.files = [], []
        if self.is_root() and not self.is_dir():
            raise NodeError, "Root node cannot be FILE kind"

    @LazyProperty
    def parent(self):
        parent_path = self.get_parent_path()
        if parent_path:
            if self.changeset:
                return self.changeset.get_node(parent_path)
            return DirNode(parent_path)
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

class FileNode(Node):
    """
    Class representing file nodes.

    :attribute: path: path to the node, relative to repostiory's root
    :attribute: content: if given arbitrary sets content of the file
    :attribute: changeset: if given, first time content is accessed, callback
    """

    def __init__(self, path, content=None, changeset=None):
        """
        Only one of ``content`` and ``changeset`` may be given. Passing both
        would raise ``NodeError`` exception.

        :param path: relative path to the node
        :param content: content may be passed to constructor
        :param changeset: if given, will use it to lazily fetch content
        """

        if content and changeset:
            raise NodeError("Cannot use both content and changeset")
        super(FileNode, self).__init__(path, kind=NodeKind.FILE)
        self.changeset = changeset
        self._content = content

    @LazyProperty
    def content(self):
        if self.changeset:
            return self.changeset.get_file_content(self.path)
        else:
            return self._content

    @LazyProperty
    def nodes(self):
        raise NodeError("%s represents a file and has no ``nodes`` attribute"
            % self)

    @LazyProperty
    def size(self):
        if self.changeset:
            return self.changeset.get_file_size(self.path)
        raise NodeError("Cannot retrieve size of the file without related "
            "changeset attribute")

    @LazyProperty
    def message(self):
        if self.changeset:
            return self.changeset.get_file_message(self.path)
        raise NodeError("Cannot retrieve message of the file without related "
            "changeset attribute")

    @LazyProperty
    def last_changeset(self):
        if self.changeset:
            return self.changeset.get_file_changeset(self.path)
        raise NodeError("Cannot retrieve last changeset of the file without "
            "related changeset attribute")

    @LazyProperty
    def mimetype(self):
        """
        Mimetype is calculated based on the file's content. If ``_mimetype``
        attribute is available, it will be returned (backends which store
        mimetypes or can easily recognize them, should set this private
        attribute to indicate that type should *NOT* be calculated).
        """
        if hasattr(self, '_mimetype'):
            return self._mimetype
        mtype = mimetypes.guess_type(self.name)[0]
        if mtype is None:
            try:
                self.content.decode('utf-8')
                mtype = 'text/plain'
            except UnicodeDecodeError:
                #logging.warning("Cannot decode %s!" % self)
                mtype = 'application/octet-stream'
        return mtype

    @LazyProperty
    def lexer(self):
        """
        Returns pygment's lexer class. Would try to guess lexer taking file's
        content, name and mimetype.
        """
        from pygments import lexers
        try:
            lexer = lexers.guess_lexer_for_filename(self.name, self.content)
        except lexers.ClassNotFound:
            lexer = lexers.TextLexer
        # returns first alias
        return lexer

    @LazyProperty
    def lexer_alias(self):
        """
        Returns first alias of the lexer guessed for this file.
        """
        return self.lexer.aliases[0]

class DirNode(Node):
    """
    DirNode stores list of files and directories within this node.
    Nodes may be used standalone but within repository context they
    lazily fetch data within same repositorty's changeset.
    """

    def __init__(self, path, nodes=(), changeset=None):
        """
        Only one of ``nodes`` and ``changeset`` may be given. Passing both
        would raise ``NodeError`` exception.

        :param path: relative path to the node
        :param nodes: content may be passed to constructor
        :param changeset: if given, will use it to lazily fetch content
        :param size: always 0 for ``DirNode``
        """
        if nodes and changeset:
            raise NodeError("Cannot use both nodes and changeset")
        super(DirNode, self).__init__(path, NodeKind.DIR)
        self.changeset = changeset
        self._nodes = nodes
        self.size = 0

    @LazyProperty
    def content(self):
        raise NodeError("%s represents a dir and has no ``content`` attribute"
            % self)

    @LazyProperty
    def nodes(self):
        if self.changeset:
            nodes = self.changeset.get_nodes(self.path)
        else:
            nodes = self._nodes
        self._nodes_dict = dict((node.path, node) for node in nodes)
        return sorted(nodes)

    @LazyProperty
    def files(self):
        return sorted((node for node in self.nodes if node.is_file()))

    @LazyProperty
    def dirs(self):
        return sorted((node for node in self.nodes if node.is_dir()))

    def __iter__(self):
        for node in self.nodes:
            yield node

    def get_node(self, path):
        """
        Returns node from within this particular ``DirNode``, so it is now
        allowed to fetch, i.e. node located at 'docs/api/index.rst' from node
        'docs'. In order to access deeper nodes one must fetch nodes between
        them first - this would work::

           docs = root.get_node('docs')
           docs.get_node('api').get_node('index.rst')

        :param: path - relative to the current node

        .. note::
           To access lazily (as in example above) node have to be initialized
           with related changeset object - without it node is out of context and
           may know nothing about anything else than nearest (located at same
           level) nodes.
        """
        try:
            path = path.rstrip('/')
            if path == '':
                raise NodeError("Cannot retrieve node without path")
            self.nodes # access nodes first in order to set _nodes_dict
            paths = path.split('/')
            if len(paths) == 1:
                if not self.is_root():
                    path = '/'.join((self.path, paths[0]))
                else:
                    path = paths[0]
                return self._nodes_dict[path]
            elif len(paths) > 1:
                if self.changeset is None:
                    raise NodeError("Cannot access deeper nodes without changeset")
                else:
                    path1, path2 = paths[0], '/'.join(paths[1:])
                    return self.get_node(path1).get_node(path2)
            else:
                raise KeyError
        except KeyError:
            raise NodeError("Node does not exist at %s" % path)

class RootNode(DirNode):
    """
    DirNode being the root node of the repository.
    """

    def __init__(self, nodes=(), changeset=None):
        super(RootNode, self).__init__(path='', nodes=nodes,
            changeset=changeset)

    def __repr__(self):
        return '<%s>' % self.__class__.__name__


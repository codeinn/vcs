from vcs.utils.lazy import LazyProperty

class NodeError(Exception):
    pass

class NodeKind:
    DIR = 1
    FILE = 2

class Node(object):
    """
    Simplest class representing file or directory on repository.  Should work
    for url with or without trailing slash.
    """

    def __init__(self, url, kind):
        self.url = url
        self.kind = kind
        self.name = url.rstrip('/').split('/')[-1]
        self.dirs, self.files = [], []

    @LazyProperty
    def parent(self):
        parent_url = self.get_parent_url()
        if parent:
            return Node(parent_url)
        return None

    def __cmp__(self, other):
        """
        Comparator using name of the node, needed for quick list sorting.
        """
        return cmp(self.name, other.name)

    def __repr__(self):
        return '<Node "%r">' % self.url

    def __unicode__(self):
        return unicode(self.name)

    @staticmethod
    def get_name(url):
        """
        Returns name of the node so if its url
        then only last part is returned.
        """
        return url.split('/')[-1]

    def get_parent_url(self):
        """
        Returns node's parent url or empty string if node is root.

        Examples::
          >>> node = Node('', NodeKind.DIR).get_parent_url()
          ''
          >>> Node('/some/path', NodeKind.DIR)).get_parent_url()
          '/some/'
          >>> Node('/some/path/', NodeKind.DIR)).get_parent_url()
          '/some/'
          >>> Node('/some/longer/path/', NodeKind.DIR)).get_parent_url()
          '/some/longer/'
        """
        if not self.name:
            return ''
        node_parent_url = '/'.join(self.url.split('/')[:-1]) + '/'
        return node_parent_url

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

    def get_mimetype(self, content):
        # Use chardet/python-magic/mimetypes?
        raise NotImplementedError



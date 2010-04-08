import unittest

from vcs.nodes import Node, NodeKind, NodeError

class NodeBasicTest(unittest.TestCase):

    def test_init(self):
        """
        Cannot innitialize Node objects with url with slash at the beginning.
        """
        wrong_urls = (
            '/foo',
            '/foo/bar'
        )
        for url in wrong_urls:
            self.assertRaises(NodeError, Node, url, NodeKind.FILE)

        wrong_urls = (
            '/foo/',
            '/foo/bar/'
        )
        for url in wrong_urls:
            self.assertRaises(NodeError, Node, url, NodeKind.DIR)

    def test_name(self):
        node = Node('', NodeKind.DIR)
        self.assertEqual(node.name, '')

        node = Node('path', NodeKind.FILE)
        self.assertEqual(node.name, 'path')

        node = Node('path/', NodeKind.DIR)
        self.assertEqual(node.name, 'path')

        node = Node('some/path', NodeKind.FILE)
        self.assertEqual(node.name, 'path')

        node = Node('some/path/', NodeKind.DIR)
        self.assertEqual(node.name, 'path')

    def test_root_node(self):
        self.assertRaises(NodeError, Node, '', NodeKind.FILE)

    def test_kind_setter(self):
        node = Node('', NodeKind.DIR)
        self.assertRaises(NodeError, setattr, node, 'kind', NodeKind.FILE)

    def _test_parent_url(self, node_url, expected_parent_url):
        """
        Tests if node's parent url are properly computed.
        """
        node = Node(node_url, NodeKind.DIR)
        parent_url = node.get_parent_url()
        self.assertTrue(parent_url.endswith('/') or \
            node.is_root() and parent_url == '')
        self.assertEqual(parent_url, expected_parent_url,
            "Node's url is %r and parent url is %r but should be %r"
            % (node.url, parent_url, expected_parent_url))

    def test_parent_url(self):
        test_urls = (
            # (node_url, expected_parent_url)
            ('', ''),
            ('some/path/', 'some/'),
            ('some/longer/path/', 'some/longer/'),
        )
        for node_url, expected_parent_url in test_urls:
            self._test_parent_url(node_url, expected_parent_url)


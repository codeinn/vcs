import unittest

from vcs.nodes import Node, NodeKind, NodeError, FileNode, DirNode

class NodeBasicTest(unittest.TestCase):

    def test_init(self):
        """
        Cannot innitialize Node objects with path with slash at the beginning.
        """
        wrong_paths = (
            '/foo',
            '/foo/bar'
        )
        for path in wrong_paths:
            self.assertRaises(NodeError, Node, path, NodeKind.FILE)

        wrong_paths = (
            '/foo/',
            '/foo/bar/'
        )
        for path in wrong_paths:
            self.assertRaises(NodeError, Node, path, NodeKind.DIR)

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

    def _test_parent_path(self, node_path, expected_parent_path):
        """
        Tests if node's parent path are properly computed.
        """
        node = Node(node_path, NodeKind.DIR)
        parent_path = node.get_parent_path()
        self.assertTrue(parent_path.endswith('/') or \
            node.is_root() and parent_path == '')
        self.assertEqual(parent_path, expected_parent_path,
            "Node's path is %r and parent path is %r but should be %r"
            % (node.path, parent_path, expected_parent_path))

    def test_parent_path(self):
        test_paths = (
            # (node_path, expected_parent_path)
            ('', ''),
            ('some/path/', 'some/'),
            ('some/longer/path/', 'some/longer/'),
        )
        for node_path, expected_parent_path in test_paths:
            self._test_parent_path(node_path, expected_parent_path)

    '''
    def _test_trailing_slash(self, path):
        if not path.endswith('/'):
            self.fail("Trailing slash tests needs paths to end with slash")
        for kind in NodeKind.FILE, NodeKind.DIR:
            self.assertRaises(NodeError, Node, path=path, kind=kind)

    def test_trailing_slash(self):
        for path in ('/', 'foo/', 'foo/bar/', 'foo/bar/biz/'):
            self._test_trailing_slash(path)
    '''

    def test_is_file(self):
        node = Node('any', NodeKind.FILE)
        self.assertTrue(node.is_file())

        node = FileNode('any')
        self.assertTrue(node.is_file())
        self.assertRaises(NodeError, getattr, node, 'nodes')

    def test_is_dir(self):
        node = Node('any_dir', NodeKind.DIR)
        self.assertTrue(node.is_dir())

        node = DirNode('any_dir')

        self.assertTrue(node.is_dir())
        self.assertRaises(NodeError, getattr, node, 'content')

    def test_dir_node_iter(self):
        nodes = [
            DirNode('docs'),
            DirNode('tests'),
            FileNode('bar'),
            FileNode('foo'),
            FileNode('readme.txt'),
            FileNode('setup.py'),
        ]
        dirnode = DirNode('', nodes=nodes)
        for node in dirnode:
            node == dirnode.get_node(node.path)

if __name__ == '__main__':
    unittest.main()


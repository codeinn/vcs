import unittest

from vcs.nodes import Node, NodeKind, NodeError

class NodeBasicTest(unittest.TestCase):

    def test_name(self):
        node = Node('', NodeKind.FILE)
        self.assertTrue(node.name == '')

        node = Node('path', NodeKind.FILE)
        self.assertTrue(node.name == 'path')

        node = Node('/path', NodeKind.FILE)
        self.assertTrue(node.name == 'path')

        node = Node('/path/', NodeKind.FILE)
        self.assertTrue(node.name == 'path')

        node = Node('/some/path', NodeKind.FILE)
        self.assertTrue(node.name == 'path')

        node = Node('/some/path/', NodeKind.FILE)
        self.assertTrue(node.name == 'path')

    def test_parent_url(self):
        node = Node('', NodeKind.DIR)
        self.assertTrue(node.get_parent_url() == '')
        node = Node('/some/path', NodeKind.DIR)
        self.assertTrue(node.get_parent_url() == '/some/')
        node = Node('/some/path/', NodeKind.DIR)
        self.assertTrue(node.get_parent_url() == '/some/')
        node = Node('/some/longer/path/', NodeKind.DIR)
        self.assertTrue(node.get_parent_url() == '/some/longer/')


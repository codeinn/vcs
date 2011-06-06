"""
Tests so called "in memory changesets" commit API of vcs.
"""
import vcs
import time
import datetime
import unittest2

from conf import SCM_TESTS, get_new_dir

from vcs.exceptions import EmptyRepositoryError
from vcs.exceptions import NodeAlreadyAddedError
from vcs.exceptions import NodeAlreadyExistsError
from vcs.exceptions import NodeAlreadyRemovedError
from vcs.exceptions import NodeAlreadyChangedError
from vcs.exceptions import NodeDoesNotExistError
from vcs.exceptions import NodeNotChangedError
from vcs.nodes import FileNode


class InMemoryChangesetTestMixin(object):
    """
    This is a backend independent test case class which should be created
    with ``type`` method.

    It is required to set following attributes at subclass:

    - ``backend_alias``: alias of used backend (see ``vcs.BACKENDS``)
    - ``repo_path``: path to the repository which would be created for set of
      tests
    """

    def get_backend(self):
        return vcs.get_backend(self.backend_alias)

    def setUp(self):
        Backend = self.get_backend()
        self.repo_path = get_new_dir(str(time.time()))
        self.repo = Backend(self.repo_path, create=True)
        self.imc = self.repo.in_memory_changeset
        self.nodes = [
            FileNode('foobar', content='Foo & bar'),
            FileNode('foobar2', content='Foo & bar, doubled!'),
            FileNode('foo bar with spaces', content=''),
            FileNode('foo/bar/baz', content='Inside'),
        ]

    def test_add(self):
        rev_count = len(self.repo.revisions)
        to_add = [FileNode(node.path, content=node.content)
            for node in self.nodes]
        for node in to_add:
            self.imc.add(node)
        message = 'Added: %s' % ', '.join((node.path for node in self.nodes))
        author = str(self.__class__)
        changeset = self.imc.commit(message=message, author=author)

        newtip = self.repo.get_changeset()
        self.assertEqual(changeset, newtip)
        self.assertEqual(rev_count + 1, len(self.repo.revisions))
        self.assertEqual(newtip.message, message)
        self.assertEqual(newtip.author, author)
        self.assertTrue(not any((self.imc.added, self.imc.changed,
            self.imc.removed)))
        for node in to_add:
            self.assertEqual(newtip.get_node(node.path).content, node.content)

    def test_add_in_bulk(self):
        rev_count = len(self.repo.revisions)
        to_add = [FileNode(node.path, content=node.content)
            for node in self.nodes]
        self.imc.add(*to_add)
        message = 'Added: %s' % ', '.join((node.path for node in self.nodes))
        author = str(self.__class__)
        changeset = self.imc.commit(message=message, author=author)

        newtip = self.repo.get_changeset()
        self.assertEqual(changeset, newtip)
        self.assertEqual(rev_count + 1, len(self.repo.revisions))
        self.assertEqual(newtip.message, message)
        self.assertEqual(newtip.author, author)
        self.assertTrue(not any((self.imc.added, self.imc.changed,
            self.imc.removed)))
        for node in to_add:
            self.assertEqual(newtip.get_node(node.path).content, node.content)

    def test_add_raise_already_added(self):
        node = FileNode('foobar', content='baz')
        self.imc.add(node)
        self.assertRaises(NodeAlreadyAddedError, self.imc.add, node)

    def test_check_integrity_raise_already_exist(self):
        node = FileNode('foobar', content='baz')
        self.imc.add(node)
        self.imc.commit(message='Added foobar', author=str(self))
        self.imc.add(node)
        self.assertRaises(NodeAlreadyExistsError, self.imc.commit,
            message='new message',
            author=str(self))

    def test_change(self):
        self.test_add() # Performs first commit

        tip = self.repo.get_changeset()
        node = self.nodes[0]
        self.assertEqual(node.content, tip.get_node(node.path).content)

        # Change node's content
        node = FileNode(self.nodes[0].path, content='My **changed** content')
        self.imc.change(node)
        self.imc.commit(message='Changed %s' % node.path, author=str(self))

        newtip = self.repo.get_changeset()
        self.assertNotEqual(tip, newtip)
        self.assertNotEqual(tip.id, newtip.id)
        newnode = newtip.get_node(node.path)
        self.assertEqual(node.content, newnode.content)

    def test_change_raise_empty_repository(self):
        node = FileNode('foobar')
        self.assertRaises(EmptyRepositoryError, self.imc.change, node)

    def test_check_integrity_change_raise_node_does_not_exist(self):
        node = FileNode('foobar', content='baz')
        self.imc.add(node)
        self.imc.commit(message='Added foobar', author=str(self))
        node = FileNode('not-foobar', content='')
        self.imc.change(node)
        self.assertRaises(NodeDoesNotExistError, self.imc.commit,
            message='Changed not existing node',
            author=str(self))

    def test_change_raise_node_already_changed(self):
        node = FileNode('foobar', content='baz')
        self.imc.add(node)
        self.imc.commit(message='Added foobar', author=str(self))
        node = FileNode('foobar', content='more baz')
        self.imc.change(node)
        self.assertRaises(NodeAlreadyChangedError, self.imc.change, node)

    def test_check_integrity_change_raise_node_not_changed(self):
        self.test_add() # Performs first commit

        node = FileNode(self.nodes[0].path, content=self.nodes[0].content)
        self.imc.change(node)
        self.assertRaises(NodeNotChangedError, self.imc.commit,
            message='Trying to mark node as changed without touching it',
            author=str(self))

    def test_change_raise_node_already_removed(self):
        node = FileNode('foobar', content='baz')
        self.imc.add(node)
        self.imc.commit(message='Added foobar', author=str(self))
        self.imc.remove(FileNode('foobar'))
        self.assertRaises(NodeAlreadyRemovedError, self.imc.change, node)

    def test_remove(self):
        self.test_add() # Performs first commit

        tip = self.repo.get_changeset()
        node = self.nodes[0]
        self.assertEqual(node.content, tip.get_node(node.path).content)
        self.imc.remove(node)
        self.imc.commit(message='Removed %s' % node.path, author=str(self))

        newtip = self.repo.get_changeset()
        self.assertNotEqual(tip, newtip)
        self.assertNotEqual(tip.id, newtip.id)
        self.assertRaises(NodeDoesNotExistError, newtip.get_node, node.path)

    def test_remove_raise_node_does_not_exist(self):
        self.imc.remove(self.nodes[0])
        self.assertRaises(NodeDoesNotExistError, self.imc.commit,
            message='Trying to remove node at empty repository',
            author=str(self))

    def test_check_integrity_remove_raise_node_does_not_exist(self):
        self.test_add() # Performs first commit

        node = FileNode('no-such-file')
        self.imc.remove(node)
        self.assertRaises(NodeDoesNotExistError, self.imc.commit,
            message='Trying to remove not existing node',
            author=str(self))

    def test_remove_raise_node_already_removed(self):
        self.test_add() # Performs first commit

        node = FileNode(self.nodes[0].path)
        self.imc.remove(node)
        self.assertRaises(NodeAlreadyRemovedError, self.imc.remove, node)

    def test_remove_raise_node_already_changed(self):
        self.test_add() # Performs first commit

        node = FileNode(self.nodes[0].path, content='Bending time')
        self.imc.change(node)
        self.assertRaises(NodeAlreadyChangedError, self.imc.remove, node)

    def test_reset(self):
        self.imc.add(FileNode('foo', content='bar'))
        #self.imc.change(FileNode('baz', content='new'))
        #self.imc.remove(FileNode('qwe'))
        self.imc.reset()
        self.assertTrue(not any((self.imc.added, self.imc.changed,
            self.imc.removed)))

    def test_multiple_commits(self):
        N = 3 # number of commits to perform
        last = None
        for x in xrange(N):
            fname = 'file%s' % str(x).rjust(5, '0')
            content = 'foobar\n' * x
            node = FileNode(fname, content=content)
            self.imc.add(node)
            commit = self.imc.commit("Commit no. %s" % (x + 1), author='vcs')
            self.assertTrue(last != commit)
            last = commit

        # Check commit number for same repo
        self.assertEqual(len(self.repo.revisions), N)

        # Check commit number for recreated repo
        backend = self.get_backend()
        repo = backend(self.repo_path)
        self.assertEqual(len(repo.revisions), N)

    def test_date_attr(self):
        node = FileNode('foobar.txt', content='Foobared!')
        self.imc.add(node)
        date = datetime.datetime(1985, 1, 30, 1, 45)
        commit = self.imc.commit("Committed at time when I was born ;-)",
            author='lb', date=date)

        self.assertEqual(commit.date, date)



class BackendBaseTestCase(unittest2.TestCase):
    """
    Base test class for tests which requires repository.
    """
    backend_alias = 'hg'
    commits = [
        {
            'message': 'Initial commit',
            'author': 'Joe Doe <joe.doe@example.com>',
            'date': datetime.datetime(2010, 1, 1, 20),
            'added': [
                FileNode('foobar', content='Foobar'),
                FileNode('foobar2', content='Foobar II'),
                FileNode('foo/bar/baz', content='baz here!'),
            ],
        },
    ]


    def get_backend(self):
        return vcs.get_backend(self.backend_alias)

    def get_commits(self):
        """
        Returns list of commits which builds repository for each tests.
        """
        if hasattr(self, 'commits'):
            return self.commits

    def get_new_repo_path(self):
        """
        Returns newly created repository's directory.
        """
        backend = self.get_backend()
        key = '%s-%s' % (backend.alias, str(time.time()))
        repo_path = get_new_dir(key)
        return repo_path

    def setUp(self):
        Backend = self.get_backend()
        self.backend_class = Backend
        self.repo_path = self.get_new_repo_path()
        self.repo = Backend(self.repo_path, create=True)
        self.imc = self.repo.in_memory_changeset

        for commit in self.get_commits():
            for node in commit.get('added', []):
                self.imc.add(FileNode(node.path, content=node.content))
            for node in commit.get('changed', []):
                self.imc.change(FileNode(node.path, content=node.content))
            for node in commit.get('removed', []):
                self.imc.remove(FileNode(node.path))
            self.imc.commit(message=commit['message'], author=commit['author'],
                date=commit['date'])

        self.tip = self.repo.get_changeset()


# For each backend create test case class
for alias in SCM_TESTS:
    attrs = {
        'backend_alias': alias,
    }
    cls_name = ''.join(('%s in memory changeset test' % alias).title().split())
    bases = (InMemoryChangesetTestMixin, unittest2.TestCase)
    globals()[cls_name] = type(cls_name, bases, attrs)


if __name__ == '__main__':
    unittest2.main()


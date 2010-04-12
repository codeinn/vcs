import unittest

from vcs.backends.hg import MercurialRepository
from vcs.exceptions import ChangesetError, RepositoryError
from vcs.nodes import NodeKind

TEST_HG_REPO = '/tmp/vcs'

class MercurialRepositoryTest(unittest.TestCase):

    def setUp(self):
        self.repo = MercurialRepository(TEST_HG_REPO)

    def test_repo_create(self):
        wrong_repo_path = '/tmp/errorrepo'
        self.assertRaises(RepositoryError, MercurialRepository,
            repo_path=wrong_repo_path)


    def test_revisions(self):
        # there are 21 revisions at bitbucket now
        # so we can assume they would be available from now on
        subset = set(range(0, 22))
        self.assertTrue(subset.issubset(set(self.repo.revisions)))

    def _test_single_changeset_cache(self, revision):
        chset = self.repo.get_changeset(revision)
        self.assertTrue(self.repo.changesets.has_key(revision))
        self.assertEqual(chset, self.repo.changesets[revision])

    def test_changesets_cache(self):
        for revision in xrange(0, 11):
            self._test_single_changeset_cache(revision)

    def test_initial_changeset(self):

        init_chset = self.repo.get_changeset(0)
        self.assertEqual(init_chset.message, 'initial import')
        self.assertEqual(init_chset.author,
            'Marcin Kuzminski <marcin@python-blog.com>')
        self.assertEqual(sorted(init_chset._file_paths),
            sorted([
                'vcs/__init__.py',
                'vcs/backends/BaseRepository.py',
                'vcs/backends/__init__.py',
            ])
        )
        self.assertEqual(sorted(init_chset._dir_paths),
            sorted(['vcs/backends', 'vcs']))

        self.assertRaises(ChangesetError, init_chset.get_node, path='foobar')

        node = init_chset.get_node('vcs/')
        self.assertTrue(hasattr(node, 'kind'))
        self.assertEqual(node.kind, NodeKind.DIR)

        node = init_chset.get_node('vcs')
        self.assertTrue(hasattr(node, 'kind'))
        self.assertEqual(node.kind, NodeKind.DIR)

        node = init_chset.get_node('vcs/__init__.py')
        self.assertTrue(hasattr(node, 'kind'))
        self.assertEqual(node.kind, NodeKind.FILE)

    def test_not_existing_changeset(self):
        self.assertRaises(RepositoryError, self.repo.get_changeset,
            self.repo.revisions[-1] + 1)

        # Small chance we ever get to this one
        revision = pow(2, 100)
        self.assertRaises(RepositoryError, self.repo.get_changeset, revision)

    def test_changeset10(self):

        chset10 = self.repo.get_changeset(10)
        README = """===
VCS
===

Various Version Control System management abstraction layer for Python.

Introduction
------------

TODO: To be written...

"""
        node = chset10.get_node('README.rst')
        self.assertEqual(node.kind, NodeKind.FILE)
        self.assertEqual(node.content, README)


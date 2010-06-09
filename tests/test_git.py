import unittest

from vcs.backends.git import GitRepository, GitChangeset
from vcs.exceptions import ChangesetError, RepositoryError
from vcs.nodes import NodeKind, NodeState, FileNode, DirNode

from conf import TEST_GIT_REPO

class GitRepositoryTest(unittest.TestCase):

    def setUp(self):
        self.repo = GitRepository(TEST_GIT_REPO)

    def test_repo_create(self):
        wrong_repo_path = '/tmp/errorrepo'
        self.assertRaises(RepositoryError, GitRepository, wrong_repo_path)

    def test_revisions(self):
        # there are 112 revisions (by now)
        # so we can assume they would be available from now on
        subset = set([
            'c1214f7e79e02fc37156ff215cd71275450cffc3',
            '38b5fe81f109cb111f549bfe9bb6b267e10bc557',
            'fa6600f6848800641328adbf7811fd2372c02ab2',
            '102607b09cdd60e2793929c4f90478be29f85a17',
            '49d3fd156b6f7db46313fac355dca1a0b94a0017',
            '2d1028c054665b962fa3d307adfc923ddd528038',
            'd7e0d30fbcae12c90680eb095a4f5f02505ce501',
            'ff7ca51e58c505fec0dd2491de52c622bb7a806b',
            'dd80b0f6cf5052f17cc738c2951c4f2070200d7f',
            '8430a588b43b5d6da365400117c89400326e7992',
            'd955cd312c17b02143c04fa1099a352b04368118',
            'f67b87e5c629c2ee0ba58f85197e423ff28d735b',
            'add63e382e4aabc9e1afdc4bdc24506c269b7618',
            'f298fe1189f1b69779a4423f40b48edf92a703fc',
            'bd9b619eb41994cac43d67cf4ccc8399c1125808',
            '6e125e7c890379446e98980d8ed60fba87d0f6d1',
            'd4a54db9f745dfeba6933bf5b1e79e15d0af20bd',
            '0b05e4ed56c802098dfc813cbe779b2f49e92500',
            '191caa5b2c81ed17c0794bf7bb9958f4dcb0b87e',
            '45223f8f114c64bf4d6f853e3c35a369a6305520',
            'ca1eb7957a54bce53b12d1a51b13452f95bc7c7e',
            'f5ea29fc42ef67a2a5a7aecff10e1566699acd68',
            '27d48942240f5b91dfda77accd2caac94708cc7d',
            '622f0eb0bafd619d2560c26f80f09e3b0b0d78af',
            'e686b958768ee96af8029fe19c6050b1a8dd3b2b'])
        self.assertTrue(subset.issubset(set(self.repo.revisions)))

    def test_branches(self):
        # TODO: Need more tests here
        self.assertTrue('master' in self.repo.branches)
        self.assertTrue('gittree' in self.repo.branches)
        self.assertTrue('web-branch' in self.repo.branches)
        for name, id in self.repo.branches.items():
            self.assertTrue(isinstance(
                self.repo.get_changeset(id), GitChangeset))

    def test_tags(self):
        # TODO: Need more tests here
        self.assertTrue('0.1.1' in self.repo.tags)
        self.assertTrue('0.1.2' in self.repo.tags)
        for name, id in self.repo.tags.items():
            self.assertTrue(isinstance(
                self.repo.get_changeset(id), GitChangeset))

    def _test_single_changeset_cache(self, revision):
        chset = self.repo.get_changeset(revision)
        self.assertTrue(self.repo.changesets.has_key(revision))
        self.assertTrue(chset is self.repo.changesets[revision])

    def test_changesets_cache(self):
        for revision in self.repo.revisions[:10]:
            self._test_single_changeset_cache(revision)

    def _test_request(self, path, revision):
        chset = self.repo.get_changeset(revision)
        self.assertEqual(chset.get_node(path),
            self.repo.request(path, revision))

    def test_request(self):
        """ Tests if repo.request changeset.get_node would return same """
        nodes_info = (
            ('', '50e08c506174d8645a4bb517dd122ac946a0f3bf'),
            ('README.rst', 'c877b68d18e792a66b7f4c529ea02c8f80801542'),
            ('vcs', 'ca28fc8ac7b83c5e257a5a7bcf9a0d9ace715739'),
            ('vcs/backends', 'd7e390a45f6aa96f04f5e7f583ad4f867431aa25'),
            ('vcs/backends/hg.py', '34f4dd6dd285b533e6af23f794d63603e862f613'),
        )
        for path, revision in nodes_info:
            self._test_request(path, revision)


    def test_initial_changeset(self):
        id = self.repo.revisions[0]
        init_chset = self.repo.get_changeset(id)
        self.assertEqual(init_chset.message, 'initial import')
        self.assertEqual(init_chset.author,
            'Marcin Kuzminski <marcin@python-blog.com>')
        for path in ('vcs/__init__.py',
                     'vcs/backends/BaseRepository.py',
                     'vcs/backends/__init__.py'):
            self.assertTrue(isinstance(init_chset.get_node(path), FileNode))
        for path in ('', 'vcs', 'vcs/backends'):
            self.assertTrue(isinstance(init_chset.get_node(path), DirNode))

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
            'f'*40)

    def test_changeset10(self):

        chset10 = self.repo.get_changeset(self.repo.revisions[9])
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


class GitChangesetTest(unittest.TestCase):

    def setUp(self):
        self.repo = GitRepository(TEST_GIT_REPO)

    def _test_equality(self, changeset):
        revision = changeset.revision
        self.assertEqual(changeset, self.repo.changesets[revision])

    def test_equality(self):
        revs = self.repo.revisions
        changesets = [self.repo.get_changeset(rev) for rev in revs]
        for changeset in changesets:
            self._test_equality(changeset)

    def test_default_changeset(self):
        tip = self.repo.get_changeset()
        self.assertEqual(tip, self.repo.get_changeset(None))
        self.assertEqual(tip, self.repo.get_changeset('tip'))
        self.assertEqual(tip, list(self.repo.get_changesets(limit=1))[0])

    def test_root_node(self):
        tip = self.repo.get_changeset()
        self.assertTrue(tip.root is tip.get_node(''))

    def test_lazy_fetch(self):
        """
        Test if changeset's nodes expands and are cached as we walk through
        the revision. This test is somewhat hard to write as order of tests
        is a key here. Written by running command after command in a shell.
        """
        hex = '2a13f185e4525f9d4b59882791a2d397b90d5ddc'
        self.assertTrue(hex in self.repo.revisions)
        chset = self.repo.get_changeset(hex)
        self.assertTrue(len(chset.nodes) == 0)
        root = chset.root
        self.assertTrue(len(chset.nodes) == 1)
        self.assertTrue(len(root.nodes) == 8)
        # accessing root.nodes updates chset.nodes
        self.assertTrue(len(chset.nodes) == 9)

        docs = root.get_node('docs')
        # we haven't yet accessed anything new as docs dir was already cached
        self.assertTrue(len(chset.nodes) == 9)
        self.assertTrue(len(docs.nodes) == 8)
        # accessing docs.nodes updates chset.nodes
        self.assertTrue(len(chset.nodes) == 17)

        self.assertTrue(docs is chset.get_node('docs'))
        self.assertTrue(docs is root.nodes[0])
        self.assertTrue(docs is root.dirs[0])
        self.assertTrue(docs is chset.get_node('docs'))

    def test_nodes_with_changeset(self):
        hex = '2a13f185e4525f9d4b59882791a2d397b90d5ddc'
        chset = self.repo.get_changeset(hex)
        root = chset.root
        docs = root.get_node('docs')
        self.assertTrue(docs is chset.get_node('docs'))
        api = docs.get_node('api')
        self.assertTrue(api is chset.get_node('docs/api'))
        index = api.get_node('index.rst')
        self.assertTrue(index is chset.get_node('docs/api/index.rst'))
        self.assertTrue(index is chset.get_node('docs')\
            .get_node('api')\
            .get_node('index.rst'))

    def _test_file_size(self, revision, path, size):
        node = self.repo.request(path, revision)
        self.assertTrue(node.is_file())
        self.assertEqual(node.size, size)

    def test_file_size(self):
        to_check = (
            ('c1214f7e79e02fc37156ff215cd71275450cffc3',
                'vcs/backends/BaseRepository.py', 502),
            ('d7e0d30fbcae12c90680eb095a4f5f02505ce501',
                'vcs/backends/hg.py', 854),
            ('6e125e7c890379446e98980d8ed60fba87d0f6d1',
                'setup.py', 1068),

            ('d955cd312c17b02143c04fa1099a352b04368118',
                'vcs/backends/base.py', 2921),
            ('ca1eb7957a54bce53b12d1a51b13452f95bc7c7e',
                'vcs/backends/base.py', 3936),
            ('f50f42baeed5af6518ef4b0cb2f1423f3851a941',
                'vcs/backends/base.py', 6189),
        )
        for revision, path, size in to_check:
            self._test_file_size(revision, path, size)

if __name__ == '__main__':
    unittest.main()


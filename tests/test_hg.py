import unittest

from vcs.backends.hg import MercurialRepository, MercurialChangeset
from vcs.exceptions import ChangesetError, RepositoryError
from vcs.nodes import NodeKind, NodeState

TEST_HG_REPO = '/tmp/vcs'

class MercurialRepositoryTest(unittest.TestCase):

    def setUp(self):
        self.repo = MercurialRepository(TEST_HG_REPO)

    def test_repo_create(self):
        wrong_repo_path = '/tmp/errorrepo'
        self.assertRaises(RepositoryError, MercurialRepository, wrong_repo_path)

    def test_revisions(self):
        # there are 21 revisions at bitbucket now
        # so we can assume they would be available from now on
        subset = set(range(0, 22))
        self.assertTrue(subset.issubset(set(self.repo.revisions)))

    def test_branches(self):
        chset3 = self.repo.get_changeset(3)
        self.assertEqual(chset3.branch, 'default')

        chset44 = self.repo.get_changeset(44)
        self.assertEqual(chset44.branch, 'web')

        for branch in self.repo.branches:
            self.assertTrue(isinstance(branch, MercurialChangeset))

    def test_tags(self):
        # tip is always a tag
        tip = self.repo.get_changeset()
        tip in self.repo.tags

    def _test_single_changeset_cache(self, revision):
        chset = self.repo.get_changeset(revision)
        self.assertTrue(self.repo.changesets.has_key(revision))
        self.assertEqual(chset, self.repo.changesets[revision])

    def test_changesets_cache(self):
        for revision in xrange(0, 11):
            self._test_single_changeset_cache(revision)

    def _test_request(self, path, revision):
        chset = self.repo.get_changeset(revision)
        self.assertEqual(chset.get_node(path),
            self.repo.request(path, revision))

    def test_request(self):
        """ Tests if repo.request changeset.get_node would return same """
        nodes_info = (
            ('', 'tip'),
            ('README.rst', 19),
            ('vcs', 20),
            ('vcs/backends', 21),
            ('vcs/backends/hg.py', 25),
        )
        for path, revision in nodes_info:
            self._test_request(path, revision)

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
            sorted(['', 'vcs', 'vcs/backends']))

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
        revision = pow(2, 30)
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

class MercurialChangesetTest(unittest.TestCase):

    def setUp(self):
        self.repo = MercurialRepository(TEST_HG_REPO)

    def _test_equality(self, changeset):
        revision = changeset.revision
        self.assertEqual(changeset, self.repo.changesets[revision])

    def test_equality(self):
        self.setUp()
        revs = [0, 10, 20]
        changesets = [self.repo.get_changeset(rev) for rev in revs]
        for changeset in changesets:
            self._test_equality(changeset)

    def test_default_changeset(self):
        tip = self.repo.get_changeset('tip')
        self.assertEqual(tip, self.repo.get_changeset())
        # Mercurial backend converts all given revision parameters
        # so it cannot pass following two (commented) test
        # self.assertEqual(tip, self.repo.changesets[None])
        # self.assertEqual(tip, self.repo.changesets['tip'])
        self.assertEqual(tip, self.repo.get_changeset(revision=None))
        self.assertEqual(tip, list(self.repo.get_changesets(limit=1))[0])

    def test_root_node(self):
        tip = self.repo.get_changeset('tip')
        tip.root is tip.get_node('')

    def test_lazy_fetch(self):
        """
        Test if changeset's nodes expands and are cached as we walk through
        the revision. This test is somewhat hard to write as order of tests
        is a key here. Written by running command after command in a shell.
        """
        self.setUp()
        chset = self.repo.get_changeset(45)
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
        self.setUp()
        chset = self.repo.get_changeset(45)
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

    def test_branch_and_tags(self):
        chset0 = self.repo.get_changeset(0)
        self.assertEqual(chset0.branch, 'default')
        self.assertEqual(chset0.tags, [])

        chset10 = self.repo.get_changeset(10)
        self.assertEqual(chset10.branch, 'default')
        self.assertEqual(chset10.tags, [])

        chset44 = self.repo.get_changeset(44)
        self.assertEqual(chset44.branch, 'web')

        tip = self.repo.get_changeset('tip')
        self.assertTrue('tip' in tip.tags)

    def _test_slices(self, limit, offset):
        self.setUp()
        count = self.repo.count()
        changesets = self.repo.get_changesets(limit=limit, offset=offset)
        idx = 0
        for changeset in changesets:
            idx += 1
            rev = count - offset - idx
            if idx > limit:
                self.fail("Exceeded limit already (getting revision %s, "
                    "there are %s total revisions, offset=%s, limit=%s)"
                    % (rev, count, offset, limit))
            self.assertEqual(changeset,
                self.repo.get_changeset(rev))
        result = list(self.repo.get_changesets(limit=limit, offset=offset))
        start = offset
        end = limit and offset + limit or None
        sliced = list(self.repo[start:end])
        self.failUnlessEqual(result, sliced,
            msg="Comparison failed for limit=%s, offset=%s"
            "(get_changeset returned: %s and sliced: %s"
            % (limit, offset, result, sliced))

    def test_slices(self):
        slices = (
            # (limit, offset)
            (2, 0), # should get 2 most recent changesets
            (5, 2), # should get 5 most recent changesets after first 2
        )
        for limit, offset in slices:
            self._test_slices(limit, offset)

    def _test_file_size(self, revision, path, size):
        node = self.repo.request(path, revision)
        self.assertTrue(node.is_file())
        self.assertEqual(node.size, size)

    def test_file_size(self):
        to_check = (
            (10, 'setup.py', 1068),
            (20, 'setup.py', 1106),
            (60, 'setup.py', 1074),

            (10, 'vcs/backends/base.py', 2921),
            (20, 'vcs/backends/base.py', 3936),
            (60, 'vcs/backends/base.py', 6189),
        )
        for revision, path, size in to_check:
            self._test_file_size(revision, path, size)

    def test_file_history(self):
        # we can only check if those revisions are present in the history
        # as we cannot update this test every time file is changed
        files = {
            'setup.py': [7, 18, 45, 46, 47, 69, 77],
            'vcs/nodes.py': [7, 8, 24, 26, 30, 45, 47, 49, 56, 57, 58, 59, 60,
                61, 73, 76],
            'vcs/backends/hg.py': [4, 5, 6, 11, 12, 13, 14, 15, 16, 21, 22, 23,
                26, 27, 28, 30, 31, 33, 35, 36, 37, 38, 39, 40, 41, 44, 45, 47,
                48, 49, 53, 54, 55, 58, 60, 61, 67, 68, 69, 70, 73, 77, 78, 79,
                82],
        }
        for path, revs in files.items():
            node = self.repo.request(path)
            node_revs = [chset.revision for chset in node.history]
            self.assertTrue(set(revs).issubset(set(node_revs)),
                "We assumed that %s is subset of revisions for which file %s "
                "has been changed, and history of that node returned: %s"
                % (revs, path, node_revs))
    def test_file_annotate(self):
        files = {
                 'vcs/backends/__init__.py': 
                  {89: {'lines_no': 31,
                        'changesets': [32, 32, 61, 32, 32, 37, 32, 32, 32, 44,
                                       37, 37, 37, 37, 45, 37, 44, 37, 37, 37,
                                       32, 32, 32, 32, 37, 32, 37, 37, 32,
                                       32, 32]},
                   20: {'lines_no': 1,
                        'changesets': [4]},
                   55: {'lines_no': 31,
                        'changesets': [32, 32, 45, 32, 32, 37, 32, 32, 32, 44,
                                       37, 37, 37, 37, 45, 37, 44, 37, 37, 37,
                                       32, 32, 32, 32, 37, 32, 37, 37, 32,
                                       32, 32]}},
                 'vcs/exceptions.py': 
                 {89: {'lines_no': 18,
                       'changesets': [16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
                                      16, 16, 17, 16, 16, 18, 18, 18]},
                  20: {'lines_no': 18,
                       'changesets': [16, 16, 16, 16, 16, 16, 16, 16, 16, 16,
                                      16, 16, 17, 16, 16, 18, 18, 18]},
                  55: {'lines_no': 18, 'changesets': [16, 16, 16, 16, 16, 16,
                                                      16, 16, 16, 16, 16, 16,
                                                      17, 16, 16, 18, 18, 18]}},
                 'MANIFEST.in': {89: {'lines_no': 5,
                                      'changesets': [7, 7, 7, 71, 71]},
                                 20: {'lines_no': 3,
                                      'changesets': [7, 7, 7]},
                                 55: {'lines_no': 3,
                                     'changesets': [7, 7, 7]}}}

        
        for fname, revision_dict in files.items():
            for rev, data in revision_dict.items():
                cs = self.repo.get_changeset(rev)
                ann = cs.get_file_annotate(fname)

                l1 = [x[1].revision for x in ann]
                l2 = files[fname][rev]['changesets']
                self.assertTrue(l1 == l2 , "The lists of revision for %s@rev%s"
                                "from annotation list should match each other," 
                                "got \n%s \nvs \n%s " % (fname, rev, l1, l2))
                
    def test_changeset_state(self):
        """
        Tests which files have been added/changed/removed at particular revision
        """
        # 88, 85, 82, 68, 64
        # 88:
        #    added:   0
        #    changed: 1 ['.hgignore']
        #    removed: 0
        chset88 = self.repo.get_changeset(88)
        self.assertEqual(set((node.path for node in chset88.added)), set())
        self.assertEqual(set((node.path for node in chset88.changed)),
            set(['.hgignore']))
        self.assertEqual(set((node.path for node in chset88.removed)), set())

        # 85:
        #    added:   2 ['vcs/utils/diffs.py', 'vcs/web/simplevcs/views/diffs.py']
        #    changed: 4 ['vcs/web/simplevcs/models.py', ...]
        #    removed: 1 ['vcs/utils/web.py']
        chset85 = self.repo.get_changeset(85)
        self.assertEqual(set((node.path for node in chset85.added)), set([
            'vcs/utils/diffs.py',
            'vcs/web/simplevcs/views/diffs.py']))
        self.assertEqual(set((node.path for node in chset85.changed)), set([
            'vcs/web/simplevcs/models.py',
            'vcs/web/simplevcs/utils.py',
            'vcs/web/simplevcs/views/__init__.py',
            'vcs/web/simplevcs/views/repository.py',
            ]))
        self.assertEqual(set((node.path for node in chset85.removed)),
            set(['vcs/utils/web.py']))

        # 64:
        #    added:   0
        #    changed: 1 ['.hgignore']
        #    removed: 20
        chset64 = self.repo.get_changeset(64)
        self.assertEqual(set((node.path for node in chset64.added)), set())
        self.assertEqual(set((node.path for node in chset64.changed)),
            set(['vcs/backends/base.py']))
        self.assertTrue('docs/api.rst' in
            [node.path for node in chset64.removed])
        self.assertEqual(20, len(chset64.removed))

    def test_files_state(self):
        """
        Tests state of FileNodes.
        """
        node = self.repo.request('vcs/utils/diffs.py', 85)
        self.assertTrue(node.state, NodeState.ADDED)
        self.assertTrue(node.added)
        self.assertFalse(node.changed)
        self.assertFalse(node.not_changed)
        self.assertFalse(node.removed)

        node = self.repo.request('.hgignore', 88)
        self.assertTrue(node.state, NodeState.CHANGED)
        self.assertFalse(node.added)
        self.assertTrue(node.changed)
        self.assertFalse(node.not_changed)
        self.assertFalse(node.removed)

        node = self.repo.request('setup.py', 85)
        self.assertTrue(node.state, NodeState.NOT_CHANGED)
        self.assertFalse(node.added)
        self.assertFalse(node.changed)
        self.assertTrue(node.not_changed)
        self.assertFalse(node.removed)

        # If node has REMOVED state then trying to fetch it would raise
        # ChangesetError exception
        self.assertRaises(ChangesetError,
            self.repo.request, 'vcs/utils/web.py', 85)


if __name__ == '__main__':
    unittest.main()


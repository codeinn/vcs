import unittest

from vcs.backends.hg import MercurialRepository

TEST_HG_REPO = '/tmp/vcs'

class MercurialRepositoryTest(unittest.TestCase):

    def setUp(self):
        self.repo = MercurialRepository(TEST_HG_REPO)

    def test_revisions(self):
        # there are 21 revisions at bitbucket now
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
        self.assertEqual(sorted(init_chset.files),
            sorted([
                'vcs/__init__.py',
                'vcs/backends/BaseRepository.py',
                'vcs/backends/__init__.py',
            ])
        )
        self.assertEqual(sorted(init_chset.dirs),
            sorted(['vcs/backends', 'vcs']))


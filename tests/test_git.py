import unittest

from vcs.backends.git import GitRepository, GitChangeset
from vcs.exceptions import ChangesetError, RepositoryError
from vcs.nodes import NodeKind, NodeState

# from http://github.com/lukaszb/django-sorting
# git clone git@github.com:lukaszb/django-sorting.git
# we should use vcs (so we first need to mirror it, preferably at github)
TEST_GIT_REPO = '/tmp/django-sorting/'

class GitRepositoryTest(unittest.TestCase):

    def setUp(self):
        self.repo = GitRepository(TEST_GIT_REPO)

    def test_revisions(self):
        # there are 17 revisions (by now)
        # so we can assume they would be available from now on
        subset = set([
            '57e2a1b16a5c8abf5cb9056335977e84c485f7c9',
            'dfca47c70af67b257977b0ead51a1cec2d437dab',
            '637b02c8636a49802ee0b72253cbbcfc4f10f8d5',
            '209f6639cbce196bdc10aced1959935d254257ff',
            '2b256782b2c598d56675f24314efabc7c50ab67a',
            '62cbdabdb0622b5531a6cf15b748042d298eb4a5',
            '5bbd21a2420df3729db23c3a77ee818d850ad4c5',
            'ce60eaf974f970f192597fdabc98eb1193ba57d6',
            '0867e9e27a76d3ca3275477f9c34c3d4558bdfb9',
            '81ce9735ae5fe9dcf00b12aa8287d30b225639f5',
            'bb3d4102965b0e4b30587b3157e9a2647abf3573',
            '39376fe1f5e50d01f7b45de949de3affa18fbc6f',
            '5558635d6656a8d4f30309bc45392184fff8595e',
            '4a9b7ef5de01316d96ef9211854f91ad4cb448d3',
            'c7e0fff07927b48076ec660d8cf1ced5b9b25112',
            '70bde520d66d725dcbf73d47b8bb212838dc9393',
            'f7ca4e4e4714b76098818596c908ce7fc2085f75'])
        self.assertTrue(subset.issubset(set(self.repo.revisions)))

class GitChangesetTest(unittest.TestCase):

    def setUp(self):
        self.repo = GitRepository(TEST_GIT_REPO)

    def _test_equality(self, changeset):
        revision = changeset.revision
        self.assertEqual(changeset, self.repo.changesets[revision])

    def test_equality(self):
        self.setUp()
        revs = self.repo.revisions
        changesets = [self.repo.get_changeset(rev) for rev in revs]
        for changeset in changesets:
            self._test_equality(changeset)


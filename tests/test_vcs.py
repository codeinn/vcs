import unittest2

from vcs import VCSError, get_repo, get_backend
from vcs.backends.hg import MercurialRepository
from conf import TEST_HG_REPO

class VCSTest(unittest2.TestCase):
    """
    Tests for main module's methods.
    """

    def test_get_backend(self):
        hg = get_backend('hg')
        self.assertEqual(hg, MercurialRepository)

    def test_wrong_alias(self):
        alias = 'wrong_alias'
        self.assertRaises(VCSError, get_backend, alias)

    def test_get_repo(self):
        alias = 'hg'
        path = TEST_HG_REPO
        backend = get_backend(alias)
        repo = backend(path)

        self.assertEqual(repo.__class__, get_repo(alias, path).__class__)
        self.assertEqual(repo.path, get_repo(alias, path).path)


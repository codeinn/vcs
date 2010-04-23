import unittest

from vcs import VCSError, get_repo, get_backend
from vcs.backends.hg import MercurialRepository

class VCSTest(unittest.TestCase):
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
        path = '/tmp/vcs'
        backend = get_backend(alias)
        repo = backend(path)

        self.assertEqual(repo.__class__, get_repo(alias, path).__class__)
        self.assertEqual(repo.path, get_repo(alias, path).path)

if __name__ == '__main__':
    unittest.main()


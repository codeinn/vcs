import unittest

from vcs import VCSError, get_repo
from vcs.backends.hg import MercurialRepository

class VCSTest(unittest.TestCase):
    """
    Tests for main module's methods.
    """

    def test_get_repo(self):
        hg = get_repo('hg')
        self.assertEqual(hg, MercurialRepository)

    def test_wrong_alias(self):
        alias = 'wrong_alias'
        self.assertRaises(VCSError, get_repo, alias)


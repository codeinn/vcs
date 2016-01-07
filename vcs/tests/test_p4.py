import unittest
import logging

import datetime

from vcs.backends.p4.repository import P4Repository

TEST_P4_REPO = '//depot/Tools/p4sandbox/...'


class P4RepositoryTest(unittest.TestCase):
	"""
	These tests work only in Michel's repository, they should be changed so they first create some commits on
	a sandbox server and then query these commits.
	"""
	def setUp(self):
		self.repo = P4Repository(TEST_P4_REPO)
		logging.basicConfig(level=logging.DEBUG)

	def test_get_changelists(self):
		CLs = self.repo.get_changesets()

		for cl in CLs:
			logging.debug('%s, %s', cl, cl.time)

		self.assertEqual(len(CLs), 5)

	def test_get_changelists_range(self):
		CLs = self.repo.get_changesets(start_date=datetime.datetime(2013,5,3,3))

		for cl in CLs:
			logging.debug('%s, %s', cl, cl.time)

		self.assertEqual(len(CLs), 2)


if __name__ == '__main__':
	unittest.main()

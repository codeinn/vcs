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

	def test_get_changelists_end_date_only(self):
		CLs = self.repo.get_changesets(end_date=datetime.datetime(2014, 1, 1))

		for cl in CLs:
			logging.debug('%s, %s', cl, cl.date)

		self.assertEqual(len(CLs), 5)

	def test_get_changelists_range(self):
		CLs = self.repo.get_changesets(start_date=datetime.datetime(2013, 5, 3, 3),
									   end_date=datetime.datetime(2014, 1, 1))

		for cl in CLs:
			logging.debug('%s, %s', cl, cl.date)

		self.assertEqual(len(CLs), 2)

	def test_get_affected_files(self):
		cs = self.repo.get_changeset(562108)
		files = cs.affected_files()
		self.assertEqual(len(files), 1)
		self.assertEqual(files[0], '//depot/Tools/p4sandbox/file_to_be_added.txt')

		# changeset after obliterated files
		repo = P4Repository('//depot/...')
		cs = repo.get_changeset(24754)
		files = cs.affected_files()


if __name__ == '__main__':
	unittest.main()

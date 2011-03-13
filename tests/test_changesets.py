from __future__ import with_statement

import vcs
import datetime
import unittest2
from base import BackendTestMixin
from conf import SCM_TESTS
from vcs.nodes import FileNode
from vcs.exceptions import BranchDoesNotExistError
from vcs.exceptions import ChangesetDoesNotExistError
from vcs.exceptions import RepositoryError


class ChangesetsWithCommitsTestCaseixin(BackendTestMixin):
    recreate_repo_per_test = True

    @classmethod
    def _get_commits(cls):
        start_date = datetime.datetime(2010, 1, 1, 20)
        for x in xrange(5):
            yield {
                'message': 'Commit %d' % x,
                'author': 'Joe Doe <joe.doe@example.com>',
                'date': start_date + datetime.timedelta(hours=12 * x),
                'added': [
                    FileNode('file_%d.txt' % x, content='Foobar %d' % x),
                ],
            }

    def test_new_branch(self):
        self.imc.add(vcs.nodes.FileNode('docs/index.txt',
            content='Documentation\n'))
        foobar_tip = self.imc.commit(
            message='New branch: foobar',
            author='joe',
            branch='foobar',
        )
        self.assertTrue('foobar' in self.repo.branches)
        self.assertEqual(foobar_tip.branch, 'foobar')

    def test_new_head_in_default_branch(self):
        tip = self.repo.get_changeset()
        self.imc.add(vcs.nodes.FileNode('docs/index.txt',
            content='Documentation\n'))
        foobar_tip = self.imc.commit(
            message='New branch: foobar',
            author='joe',
            branch='foobar',
            parents=[tip],
        )
        self.imc.change(vcs.nodes.FileNode('docs/index.txt',
            content='Documentation\nand more...\n'))
        newtip = self.imc.commit(
            message='At default branch',
            author='joe',
            branch=foobar_tip.branch,
            parents=[foobar_tip],
        )

        newest_tip = self.imc.commit(
            message='Merged with %s' % foobar_tip.raw_id,
            author='joe',
            branch=self.backend_class.DEFAULT_BRANCH_NAME,
            parents=[newtip, foobar_tip],
        )

        self.assertEqual(newest_tip.branch,
            self.backend_class.DEFAULT_BRANCH_NAME)

    def test_get_changesets_respects_branch_name(self):
        tip = self.repo.get_changeset()
        self.imc.add(vcs.nodes.FileNode('docs/index.txt',
            content='Documentation\n'))
        doc_changeset = self.imc.commit(
            message='New branch: docs',
            author='joe',
            branch='docs',
        )
        self.imc.add(vcs.nodes.FileNode('newfile', content=''))
        self.imc.commit(
            message='Back in default branch',
            author='joe',
            parents=[tip],
        )
        default_branch_changesets = self.repo.get_changesets(
            branch_name=self.repo.DEFAULT_BRANCH_NAME)
        self.assertNotIn(doc_changeset, default_branch_changesets)


class ChangesetsTestCaseMixin(BackendTestMixin):
    recreate_repo_per_test = False

    @classmethod
    def _get_commits(cls):
        start_date = datetime.datetime(2010, 1, 1, 20)
        for x in xrange(5):
            yield {
                'message': 'Commit %d' % x,
                'author': 'Joe Doe <joe.doe@example.com>',
                'date': start_date + datetime.timedelta(hours=12 * x),
                'added': [
                    FileNode('file_%d.txt' % x, content='Foobar %d' % x),
                ],
            }

    def test_simple(self):
        tip = self.repo.get_changeset()
        self.assertEqual(tip.date, datetime.datetime(2010, 1, 3, 20))

    def test_get_changesets_is_ordered_by_date(self):
        changesets = list(self.repo.get_changesets())
        ordered_by_date = sorted(changesets,
            key=lambda cs: cs.date)
        self.assertItemsEqual(changesets, ordered_by_date)

    def test_get_changesets_respects_start(self):
        second_id = self.repo.revisions[1]
        changesets = list(self.repo.get_changesets(start=second_id))
        self.assertEqual(len(changesets), 4)

    def test_get_changesets_includes_start_changeset(self):
        second_id = self.repo.revisions[1]
        changesets = list(self.repo.get_changesets(start=second_id))
        self.assertEqual(changesets[0].raw_id, second_id)

    def test_get_changesets_respects_end(self):
        second_id = self.repo.revisions[1]
        changesets = list(self.repo.get_changesets(end=second_id))
        self.assertEqual(changesets[-1].raw_id, second_id)
        self.assertEqual(len(changesets), 2)

    def test_get_changesets_includes_end_changeset(self):
        second_id = self.repo.revisions[1]
        changesets = list(self.repo.get_changesets(end=second_id))
        self.assertEqual(changesets[-1].raw_id, second_id)

    def test_get_changesets_respects_start_date(self):
        start_date = datetime.datetime(2010, 2, 1)
        for cs in self.repo.get_changesets(start_date=start_date):
            self.assertGreaterEqual(cs.date, start_date)

    def test_get_changesets_respects_end_date(self):
        end_date = datetime.datetime(2010, 2, 1)
        for cs in self.repo.get_changesets(end_date=end_date):
            self.assertLessEqual(cs.date, end_date)

    def test_get_changesets_respects_reverse(self):
        changesets_id_list = [cs.raw_id for cs in
            self.repo.get_changesets(reverse=True)]
        self.assertItemsEqual(changesets_id_list, reversed(self.repo.revisions))

    def test_get_changesets_raise_changesetdoesnotexist_for_wrong_start(self):
        with self.assertRaises(ChangesetDoesNotExistError):
            list(self.repo.get_changesets(start='foobar'))

    def test_get_changesets_raise_changesetdoesnotexist_for_wrong_end(self):
        with self.assertRaises(ChangesetDoesNotExistError):
            list(self.repo.get_changesets(end='foobar'))

    def test_get_changesets_raise_branchdoesnotexist_for_wrong_branch_name(self):
        with self.assertRaises(BranchDoesNotExistError):
            list(self.repo.get_changesets(branch_name='foobar'))

    def test_get_changesets_raise_repositoryerror_for_wrong_start_end(self):
        start = self.repo.revisions[-1]
        end = self.repo.revisions[0]
        with self.assertRaises(RepositoryError):
            list(self.repo.get_changesets(start=start, end=end))

# For each backend create test case class
for alias in SCM_TESTS:
    attrs = {
        'backend_alias': alias,
    }
    # tests with additional commits
    cls_name = ''.join(('%s changesets with commits test' % alias).title().split())
    bases = (ChangesetsWithCommitsTestCaseixin, unittest2.TestCase)
    globals()[cls_name] = type(cls_name, bases, attrs)

    # tests without additional commits
    cls_name = ''.join(('%s changesets test' % alias).title().split())
    bases = (ChangesetsTestCaseMixin, unittest2.TestCase)
    globals()[cls_name] = type(cls_name, bases, attrs)


if __name__ == '__main__':
    unittest2.main()


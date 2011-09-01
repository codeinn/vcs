from __future__ import with_statement

import datetime
from vcs.nodes import FileNode
from vcs.utils.compat import unittest
from base import BackendTestMixin
from conf import SCM_TESTS


class WorkdirTestCaseMixin(BackendTestMixin):

    @classmethod
    def _get_commits(cls):
        commits = [
            {
                'message': 'Initial commit',
                'author': 'Joe Doe <joe.doe@example.com>',
                'date': datetime.datetime(2010, 1, 1, 20),
                'added': [
                    FileNode('foobar', content='Foobar'),
                    FileNode('foobar2', content='Foobar II'),
                    FileNode('foo/bar/baz', content='baz here!'),
                ],
            },
            {
                'message': 'Changes...',
                'author': 'Jane Doe <jane.doe@example.com>',
                'date': datetime.datetime(2010, 1, 1, 21),
                'added': [
                    FileNode('some/new.txt', content='news...'),
                ],
                'changed': [
                    FileNode('foobar', 'Foobar I'),
                ],
                'removed': [],
            },
        ]
        return commits


    def test_get_branch_for_default_branch(self):
        self.assertEqual(self.repo.workdir.get_branch(),
            self.repo.DEFAULT_BRANCH_NAME)

    def test_get_branch_after_adding_one(self):
        self.imc.add(FileNode('docs/index.txt',
            content='Documentation\n'))
        self.imc.commit(
            message='New branch: foobar',
            author='joe',
            branch='foobar',
        )
        self.assertEqual(self.repo.workdir.get_branch(), 'foobar')

    def test_get_changeset(self):
        self.imc.add(FileNode('docs/index.txt',
            content='Documentation\n'))
        head = self.imc.commit(
            message='New branch: foobar',
            author='joe',
            branch='foobar',
        )
        self.assertEqual(self.repo.workdir.get_changeset(), head)

    def test_checkout_branch(self):
        from vcs.exceptions import BranchDoesNotExistError
        # first, 'foobranch' does not exist.
        self.assertRaises(BranchDoesNotExistError, self.repo.workdir.checkout_branch,
                          branch='foobranch')
        # create new branch 'foobranch'.
        self.imc.add(FileNode('file1', content='blah'))
        foobranch_head = self.imc.commit(message='asd', author='john', branch='foobranch')
        # go back to the default branch
        self.repo.workdir.checkout_branch()
        self.assertEqual(self.repo.workdir.get_branch(), self.backend_class.DEFAULT_BRANCH_NAME)
        self.assertEqual(self.repo.workdir.get_changeset(), self.tip)
        # checkout 'foobranch'
        self.repo.workdir.checkout_branch('foobranch')
        self.assertEqual(self.repo.workdir.get_branch(), 'foobranch')
        self.assertEqual(self.repo.workdir.get_changeset(), foobranch_head)


# For each backend create test case class
for alias in SCM_TESTS:
    attrs = {
        'backend_alias': alias,
    }
    cls_name = ''.join(('%s branch test' % alias).title().split())
    bases = (WorkdirTestCaseMixin, unittest.TestCase)
    globals()[cls_name] = type(cls_name, bases, attrs)


if __name__ == '__main__':
    unittest.main()


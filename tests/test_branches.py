import vcs
import datetime
import unittest2

from base import BackendTestMixin
from conf import SCM_TESTS

from vcs.nodes import FileNode


class BranchesTestCaseMixin(BackendTestMixin):

    def _get_commits(self):
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

    def test_simple(self):
        tip = self.repo.get_changeset()
        self.assertEqual(tip.date, datetime.datetime(2010, 1, 1, 21))

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


# For each backend create test case class
for alias in SCM_TESTS:
    attrs = {
        'backend_alias': alias,
    }
    cls_name = ''.join(('%s branch test' % alias).title().split())
    bases = (BranchesTestCaseMixin, unittest2.TestCase)
    globals()[cls_name] = type(cls_name, bases, attrs)


if __name__ == '__main__':
    unittest2.main()


import vcs
import unittest2

from base import BackendTestMixin
from conf import SCM_TESTS


class BranchesTestCaseMixin(BackendTestMixin):

    def test_simple(self):
        pass

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


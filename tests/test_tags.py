import unittest2

from base import BackendTestMixin
from conf import SCM_TESTS

from vcs.exceptions import TagAlreadyExistError


class TagsTestCaseMixin(BackendTestMixin):

    def test_tag(self):
        tip = self.repo.get_changeset()
        tag = self.repo.tag('last-commit', 'joe', tip.raw_id)

        for top, dirs, files in tip.walk():
            self.assertEqual(top, tag.get_node(top.path))

    def test_tag_already_exist(self):
        tip = self.repo.get_changeset()
        self.repo.tag('last-commit', 'joe', tip.raw_id)

        self.assertRaises(TagAlreadyExistError,
            self.repo.tag, 'last-commit', 'joe', tip.raw_id)

        chset = self.repo.get_changeset(0)
        self.assertRaises(TagAlreadyExistError,
            self.repo.tag, 'last-commit', 'jane', chset.raw_id)


# For each backend create test case class
for alias in SCM_TESTS:
    attrs = {
        'backend_alias': alias,
    }
    cls_name = ''.join(('%s tags test' % alias).title().split())
    bases = (TagsTestCaseMixin, unittest2.TestCase)
    globals()[cls_name] = type(cls_name, bases, attrs)


if __name__ == '__main__':
    unittest2.main()


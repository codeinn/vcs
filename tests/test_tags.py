import unittest2

from base import BackendTestMixin
from conf import SCM_TESTS

from vcs.exceptions import TagAlreadyExistError
from vcs.exceptions import TagDoesNotExistError


class TagsTestCaseMixin(BackendTestMixin):

    def test_new_tag(self):
        tip = self.repo.get_changeset()
        tagsize = len(self.repo.tags)
        tag = self.repo.tag('last-commit', 'joe', tip.raw_id)

        self.assertEqual(len(self.repo.tags), tagsize + 1)
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

    def test_remove_tag(self):
        tip = self.repo.get_changeset()
        self.repo.tag('last-commit', 'joe', tip.raw_id)
        tagsize = len(self.repo.tags)

        self.repo.remove_tag('last-commit', user='evil joe')
        self.assertEqual(len(self.repo.tags), tagsize - 1)

    def test_remove_tag_which_does_not_exist(self):
        self.assertRaises(TagDoesNotExistError,
            self.repo.remove_tag, 'last-commit', user='evil joe')

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


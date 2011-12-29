from __future__ import with_statement
from base import BackendTestMixin
from conf import SCM_TESTS
from vcs.utils.compat import unittest

from conf import TEST_USER_CONFIG_FILE

class RepositoryBaseTest(BackendTestMixin):
    recreate_repo_per_test = False

    @classmethod
    def _get_commits(cls):
        return super(RepositoryBaseTest, cls)._get_commits()[:1]

    def test_get_config_value(self):
        self.assertEqual(self.repo.get_config_value('universal', 'foo',
            TEST_USER_CONFIG_FILE), 'bar')

    def test_get_config_value_defaults_to_None(self):
        self.assertEqual(self.repo.get_config_value('universal', 'nonexist',
            TEST_USER_CONFIG_FILE), None)

    def test_get_user_name(self):
        self.assertEqual(self.repo.get_user_name(TEST_USER_CONFIG_FILE),
            'Foo Bar')

    def test_get_user_email(self):
        self.assertEqual(self.repo.get_user_email(TEST_USER_CONFIG_FILE),
            'foo.bar@example.com')


# For each backend create test case class
for alias in SCM_TESTS:
    attrs = {
        'backend_alias': alias,
    }
    cls_name = alias.capitalize() + RepositoryBaseTest.__name__
    bases = (RepositoryBaseTest, unittest.TestCase)
    globals()[cls_name] = type(cls_name, bases, attrs)


if __name__ == '__main__':
    unittest.main()


import unittest2

from vcs.utils.paths import get_dirs_for_path
from vcs.utils.helpers import get_scm

from conf import TEST_HG_REPO, TEST_GIT_REPO, TEST_TMP_PATH
from vcs.exceptions import VCSError

import os
import shutil

class PathsTest(unittest2.TestCase):

    def _test_get_dirs_for_path(self, path, expected):
        """
        Tests if get_dirs_for_path returns same as expected.
        """
        expected = sorted(expected)
        result = sorted(get_dirs_for_path(path))
        self.assertEqual(result, expected,
            msg="%s != %s which was expected result for path %s"
            % (result, expected, path))

    def test_get_dirs_for_path(self):
        path = 'foo/bar/baz/file'
        paths_and_results = (
            ('foo/bar/baz/file', ['foo', 'foo/bar', 'foo/bar/baz']),
            ('foo/bar/', ['foo', 'foo/bar']),
            ('foo/bar', ['foo']),
        )
        for path, expected in paths_and_results:
            self._test_get_dirs_for_path(path, expected)


    def test_get_scm(self):
        self.assertEqual(('hg', TEST_HG_REPO), get_scm(TEST_HG_REPO))
        self.assertEqual(('git', TEST_GIT_REPO), get_scm(TEST_GIT_REPO))

    def test_get_two_scms_for_path(self):
        multialias_repo_path = os.path.join(TEST_TMP_PATH, 'hg-git-repo-2')
        if os.path.isdir(multialias_repo_path):
            shutil.rmtree(multialias_repo_path)

        os.mkdir(multialias_repo_path)

        self.assertRaises(VCSError, get_scm, multialias_repo_path)

    def test_get_scm_error_path(self):
        self.assertRaises(VCSError, get_scm, 'err')

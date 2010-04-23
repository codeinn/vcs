import unittest

from vcs.utils.paths import get_dirs_for_path

class PathsTest(unittest.TestCase):

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

if __name__ == '__main__':
    unittest.main()


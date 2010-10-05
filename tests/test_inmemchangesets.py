"""
Tests so called "in memory changesets" commit API of vcs.
"""
import vcs
import unittest2

from conf import SCM_TESTS, get_new_dir

from vcs.exceptions import RepositoryError
from vcs.nodes import FileNode


class InMemoryChangesetTestMixin(object):
    """
    This is a backend independent test case class which should be created
    with ``type`` method.

    It is required to set following attributes at subclass:

    - ``backend_alias``: alias of used backend (see ``vcs.BACKENDS``)
    - ``repo_path``: path to the repository which would be created for set of
      tests
    """

    def get_backend(self):
        return vcs.get_backend(self.backend_alias)

    def setUp(self):
        Backend = self.get_backend()
        try:
            self.repo = Backend(self.repo_path)
        except RepositoryError:
            self.repo = Backend(self.repo_path, create=True)
        self.imc = self.repo.in_memory_changeset

    def test_add_commit(self):
        rev_count = len(self.repo.revisions)
        to_add = [
            FileNode('newfile.txt', content='Some content\n'),
            FileNode('newfile2.txt', content='Another content\n'),
        ]
        self.imc.add(*to_add)
        message = 'Added newfile.txt and newfile2.txt'
        author = str(self.__class__)
        changeset = self.imc.commit(message=message, author=author)

        newtip = self.repo.get_changeset()
        self.assertEqual(changeset, newtip)
        self.assertEqual(rev_count + 1, len(self.repo.revisions))
        self.assertEqual(newtip.message, message)
        self.assertEqual(newtip.author, author)


# For each backend create test case class
for alias in SCM_TESTS:
    attrs = {
        'backend_alias': alias,
        'repo_path': get_new_dir(alias),
    }
    cls_name = ''.join(('%s in memory changeset test' % alias).title().split())
    bases = (InMemoryChangesetTestMixin, unittest2.TestCase)
    globals()[cls_name] = type(cls_name, bases, attrs)



if __name__ == '__main__':
    unittest2.main()


import datetime
from conf import TEST_USER_CONFIG_FILE
from vcs.backends.base import EmptyChangeset
from vcs.nodes import FileNode

class RepositoryGetDiffTest(BackendTestMixin):

    @classmethod
    def _get_commits(cls):
        commits = [
            {
                'message': 'Initial commit',
                'author': 'Joe Doe <joe.doe@example.com>',
                'date': datetime.datetime(2010, 1, 1, 20),
                'added': [
                    FileNode('foobar', content='foobar'),
                    FileNode('foobar2', content='foobar2'),
                ],
            },
            {
                'message': 'Changed foobar, added foobar3',
                'author': 'Jane Doe <jane.doe@example.com>',
                'date': datetime.datetime(2010, 1, 1, 21),
                'added': [
                    FileNode('foobar3', content='foobar3'),
                ],
                'changed': [
                    FileNode('foobar', 'FOOBAR'),
                ],
            },
            {
                'message': 'Removed foobar, changed foobar3',
                'author': 'Jane Doe <jane.doe@example.com>',
                'date': datetime.datetime(2010, 1, 1, 22),
                'changed': [
                    FileNode('foobar3', content='FOOBAR\nFOOBAR\nFOOBAR\n'),
                ],
                'removed': [FileNode('foobar')],
            },
        ]
        return commits

    def test_initial_commit_diff(self):
        initial_rev = self.repo.revisions[0]
        self.assertEqual(self.repo.get_diff(EmptyChangeset, initial_rev), '''diff --git a/foobar b/foobar
new file mode 100644
index 0000000..f6ea049
--- /dev/null
+++ b/foobar
@@ -0,0 +1 @@
+foobar
\ No newline at end of file
diff --git a/foobar2 b/foobar2
new file mode 100644
index 0000000..e8c9d6b
--- /dev/null
+++ b/foobar2
@@ -0,0 +1 @@
+foobar2
\ No newline at end of file
''')

    def test_second_changeset_diff(self):
        revs = self.repo.revisions
        self.assertEqual(self.repo.get_diff(revs[0], revs[1]), '''diff --git a/foobar b/foobar
index f6ea049..389865b 100644
--- a/foobar
+++ b/foobar
@@ -1 +1 @@
-foobar
\ No newline at end of file
+FOOBAR
\ No newline at end of file
diff --git a/foobar3 b/foobar3
new file mode 100644
index 0000000..c11c37d
--- /dev/null
+++ b/foobar3
@@ -0,0 +1 @@
+foobar3
\ No newline at end of file
''')

    def test_third_changeset_diff(self):
        revs = self.repo.revisions
        self.assertEqual(self.repo.get_diff(revs[1], revs[2]), '''diff --git a/foobar b/foobar
deleted file mode 100644
index 389865b..0000000
--- a/foobar
+++ /dev/null
@@ -1 +0,0 @@
-FOOBAR
\ No newline at end of file
diff --git a/foobar3 b/foobar3
index c11c37d..f932447 100644
--- a/foobar3
+++ b/foobar3
@@ -1 +1,3 @@
-foobar3
\ No newline at end of file
+FOOBAR
+FOOBAR
+FOOBAR
''')


for alias in SCM_TESTS:
    attrs = {
        'backend_alias': alias,
    }
    cls_name = alias.capitalize() + RepositoryGetDiffTest.__name__
    bases = (RepositoryGetDiffTest, unittest.TestCase)
    globals()[cls_name] = type(cls_name, bases, attrs)

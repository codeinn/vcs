import io
import sys
import mock
from vcs.utils import unittest
from vcs.cli import ExecutionManager
from vcs.cli import BaseCommand


class TestExecutionManager(unittest.TestCase):

    def test_default_argv(self):
        with mock.patch.object(sys, 'argv', ['vcs', 'foo', 'bar']):
            manager = ExecutionManager()
            self.assertEqual(manager.argv, ['foo', 'bar'])

    def test_default_stdout(self):
        stream = io.StringIO()
        with mock.patch.object(sys, 'stdout', stream):
            manager = ExecutionManager()
            self.assertEqual(manager.stdout, stream)

    def test_default_stderr(self):
        stream = io.StringIO()
        with mock.patch.object(sys, 'stderr', stream):
            manager = ExecutionManager()
            self.assertEqual(manager.stderr, stream)

    def test_get_commands(self):
        manager = ExecutionManager()
        self.assertEqual(manager.get_commands(), ['foo', 'bar'])

    def test_get_command_class(self):
        manager = ExecutionManager()
        self.assertEqual(manager.get_command_class('foo'),
            BaseCommand)

    def test_run_command(self):
        manager = ExecutionManager(stdout=io.StringIO(),
            stderr=io.StringIO())

        class Command(BaseCommand):

            def run_from_argv(self, argv):
                self.stdout.write(u'foo')
                self.stderr.write(u'bar')

        with mock.patch.object(manager, 'get_command_class') as m:
            m.return_value = Command
            manager.run_command('cmd', manager.argv)
            self.assertEqual(manager.stdout.getvalue(), u'foo')
            self.assertEqual(manager.stderr.getvalue(), u'bar')


if __name__ == '__main__':
    unittest.main()


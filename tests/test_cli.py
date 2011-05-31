import io
import sys
import mock
import vcs.cli
from vcs.utils import unittest
from vcs.cli import BaseCommand
from vcs.cli import ExecutionManager


class TestExecutionManager(unittest.TestCase):

    def test_default_argv(self):
        with mock.patch.object(sys, 'argv', ['vcs', 'foo', 'bar']):
            manager = ExecutionManager()
            self.assertEqual(manager.argv, ['foo', 'bar'])

    def test_default_prog_name(self):
        with mock.patch.object(sys, 'argv', ['vcs', 'foo', 'bar']):
            manager = ExecutionManager()
            self.assertEqual(manager.prog_name, 'vcs')

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

    def test_get_command_class(self):
        manager = ExecutionManager()
        with mock.patch.object(vcs.cli, 'registry', {
            'foo': 'decimal.Decimal',
            'bar': 'socket.socket'}):
            from decimal import Decimal
            from socket import socket
            self.assertEqual(manager.get_command_class('foo'), Decimal)
            self.assertEqual(manager.get_command_class('bar'), socket)

    def test_get_commands(self):
        manager = ExecutionManager()
        with mock.patch.object(vcs.cli, 'registry', {
            'foo': 'vcs.cli.BaseCommand',
            'bar': 'vcs.cli.ExecutionManager'}):

            self.assertItemsEqual(manager.get_commands(), {
                'foo': BaseCommand,
                'bar': ExecutionManager,
            })

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

    def test_execute_calls_run_command_if_argv_given(self):
        manager = ExecutionManager(argv=['vcs', 'show', '-h'])
        manager.run_command = mock.Mock()
        manager.execute()
        # we also check argv passed to the command
        manager.run_command.assert_called_once_with('show', ['vcs', 'show', '-h'])

    def test_execute_calls_show_help_if_argv_not_given(self):
        manager = ExecutionManager(argv=['vcs'])
        manager.show_help = mock.Mock()
        manager.execute()
        manager.show_help.assert_called_once_with()

    def test_show_help_writes_to_stdout(self):
        manager = ExecutionManager(stdout=io.StringIO(), stderr=io.StringIO())
        manager.show_help()
        self.assertGreater(len(manager.stdout.getvalue()), 0)
        

if __name__ == '__main__':
    unittest.main()


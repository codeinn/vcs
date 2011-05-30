import sys
import vcs
from vcs.exceptions import CommandError
from optparse import make_option
from optparse import OptionParser


class ExecutionManager(object):

    def __init__(self, argv=None, stdout=None, stderr=None):
        self.prog_name = argv and argv[0] or sys.argv[0]
        self.argv = argv and argv[1:] or sys.argv[1:]
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr

    def execute(self):
        if len(self.argv) > 1:
            cmd = self.argv[0]
            argv = self.argv[1:]
            self.run_command(cmd, argv)
        else:
            self.show_help()

    def run_command(self, cmd, argv):
        Command = self.get_command_class(cmd)
        command = Command(stdout=self.stdout, stderr=self.stderr)
        command.run_from_argv(argv)
    
    def get_commands(self):
        return ['foo', 'bar']

    def get_command_class(self, cmd):
        return BaseCommand

    def show_help(self):
        output = [
            'Usage: {prog} subcommand [options] [args]'.format(
                prog=self.prog_name),
            '',
            'Available commands:',
            '',
        ]
        for cmd in self.get_commands():
            output.append('  {cmd}'.format(cmd=cmd))
        output += ['', '']
        self.stdout.write(u'\n'.join(output))
        

class BaseCommand(object):

    help = ''
    args = ''
    option_list = (
        make_option('--debug', action='store_true', dest='traceback',
            default=False, help='Enter debug mode before raising exception'),
    )

    def __init__(self, stdout=None, stderr=None):
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr

    def get_version(self):
        return vcs.get_version()

    def usage(self, subcommand):
        usage = '%%prog %s [options] %s' % (subcommand, self.args)
        return usage

    def get_parser(self, prog_name, subcommand):
        parser = OptionParser(
            prog=prog_name,
            usage=self.usage(subcommand),
            version=self.get_version(),
            option_list=self.option_list)
        return parser

    def print_help(self, prog_name, subcommand):
        parser = self.get_parser(prog_name, subcommand)
        parser.print_help()

    def run_from_argv(self, argv):
        parser = self.get_parser(argv[0], argv[1])
        options, args = parser.parse_args(argv[2:])
        self.execute(*args, **options.__dict__)

    def execute(self, *args, **options):
        try:
            self.handle(*args, **options)
        except CommandError, e:
            if options['traceback']:
                try:
                    import ipdb
                    ipdb.set_trace()
                except ImportError:
                    import pdb
                    pdb.set_trace()
            self.stderr.write('ERROR: {error}'.format(error=e))
            sys.exit(1)




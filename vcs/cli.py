import os
import sys
import vcs
from optparse import OptionParser
from optparse import make_option
from vcs.exceptions import CommandError
from vcs.exceptions import VCSError
from vcs.utils.helpers import get_scm
from vcs.utils.imports import import_class
from vcs.utils.ordered_dict import OrderedDict
from vcs.utils.paths import abspath


registry = {
    'log': 'vcs.commands.log.LogCommand',
}

class ExecutionManager(object):

    def __init__(self, argv=None, stdout=None, stderr=None):
        if argv:
            self.prog_name = argv[0]
            self.argv = argv[1:]
        else:
            self.prog_name = sys.argv[0]
            self.argv = sys.argv[1:]
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr

    def get_argv_for_command(self):
        argv = [a for a in self.argv]
        argv.insert(0, self.prog_name)
        return argv

    def execute(self):
        if len(self.argv):
            cmd = self.argv[0]
            cmd_argv = self.get_argv_for_command()
            self.run_command(cmd, cmd_argv)
        else:
            self.show_help()

    def get_command_class(self, cmd):
        cmdpath = registry[cmd]
        Command = import_class(cmdpath)
        return Command

    def get_commands(self):
        commands = OrderedDict()
        for cmd in sorted(registry.keys()):
            commands[cmd] = self.get_command_class(cmd)
        return commands

    def run_command(self, cmd, argv):
        Command = self.get_command_class(cmd)
        command = Command(stdout=self.stdout, stderr=self.stderr)
        command.run_from_argv(argv)

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
        make_option('--debug', action='store_true', dest='debug',
            default=False, help='Enter debug mode before raising exception'),
    )

    def __init__(self, stdout=None, stderr=None):
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr

    def get_version(self):
        return vcs.get_version()

    def usage(self, subcommand):
        usage = '%prog {subcommand} [options]'.format(subcommand=subcommand)
        if self.args:
            usage = '{usage} {args}'.format(usage=usage, args=self.args)
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
            if options['debug']:
                try:
                    import ipdb
                    ipdb.set_trace()
                except ImportError:
                    import pdb
                    pdb.set_trace()
            self.stderr.write('ERROR: {error}\n'.format(error=e))
            sys.exit(1)

    def handle(self, *args, **options):
        raise NotImplementedError()


class RepositoryCommand(BaseCommand):

    def __init__(self, stdout=None, stderr=None, repo=None):
        if repo is None:
            curdir = abspath(os.curdir)
            try:
                scm, path = get_scm(curdir, search_recursively=True)
                self.repo = vcs.get_repo(path, scm)
            except VCSError:
                raise CommandError('Repository not found')
        else:
            self.repo = repo
        super(RepositoryCommand, self).__init__(stdout, stderr)

    def handle(self, *args, **options):
        return self.handle_repo(self.repo, *args, **options)

    def handle_repo(self, repo, *args, **options):
        raise NotImplementedError()


class ChangesetCommand(RepositoryCommand):
    args = '<commit1> [<commit2> ...]'

    def handle_repo(self, repo, *args, **options):
        for changeset_id in args:
            changeset = repo.get_changeset(changeset_id)
            self.handle_changeset(changeset, **options)

    def handle_changeset(self, changeset, **options):
        raise NotImplementedError()


class SingleChangesetCommand(RepositoryCommand):

    option_list = RepositoryCommand.option_list + (
        make_option('-c', '--commit', action='store', dest='changeset_id',
            default=None, help='Use specific commit. By default we use HEAD/tip'),
    )

    def get_changeset(self, **options):
        cid = options.get('changeset_id', None)
        return self.repo.get_changeset(cid)


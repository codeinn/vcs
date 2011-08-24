import os
import sys
import vcs
import copy
import errno
from optparse import OptionParser
from optparse import make_option
from vcs.exceptions import CommandError
from vcs.exceptions import VCSError
from vcs.utils.helpers import get_scm
from vcs.utils.helpers import parse_changesets
from vcs.utils.helpers import parse_datetime
from vcs.utils.imports import import_class
from vcs.utils.ordered_dict import OrderedDict
from vcs.utils.paths import abspath
from vcs.utils.progressbar import ColoredProgressBar


registry = {
    'cat':      'vcs.commands.cat.CatCommand',
    'log':      'vcs.commands.log.LogCommand',
    'summary':  'vcs.commands.summary.SummaryCommand',
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
        make_option('--traceback', action='store_true', dest='traceback',
            default=False, help='Print traceback in case of an error'),
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

    def get_option_list(self):
        return self.option_list

    def get_parser(self, prog_name, subcommand):
        parser = OptionParser(
            prog=prog_name,
            usage=self.usage(subcommand),
            version=self.get_version(),
            option_list=sorted(self.get_option_list()))
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
        except Exception, e:
            if isinstance(e, IOError) and getattr(e, 'errno') == errno.EPIPE:
                sys.exit(0)
            if options['debug']:
                try:
                    import ipdb
                    ipdb.set_trace()
                except ImportError:
                    import pdb
                    pdb.set_trace()
            if options.get('traceback'):
                import traceback
                self.stderr.write(u'\n'.join((
                    '=========',
                    'TRACEBACK',
                    '=========', '', '',
                )))
                traceback.print_exc(file=self.stderr)
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
    show_progress_bar = False

    option_list = RepositoryCommand.option_list + (
        make_option('--author', action='store', dest='author',
            help='Show changes committed by specified author only.'),
        make_option('-r', '--reversed', action='store_true', dest='reversed',
            default=False, help='Iterates in asceding order.'),
        make_option('-b', '--branch', action='store', dest='branch',
            help='Narrow changesets to chosen branch. If not given, '
                 'working directory branch is used. For bare repository '
                 'default would be SCM\'s default branch (i.e. master for git)'),
        make_option('--all', action='store_true', dest='all',
            default='all', help='Show changesets across all branches.'),

        make_option('--since', '--start-date', action='store', dest='start_date',
            help='Show only changesets not younger than specified '
                 'start date.'),
        make_option('--until', '--end-date', action='store', dest='end_date',
            help='Show only changesets not older than specified '
                 'end date.'),

        make_option('--limit', action='store', dest='limit', default=None,
            help='Limit number of showed changesets.'),
    )

    def show_changeset(self, changeset, **options):
        author = options.get('author')
        if author:
            if author.startswith('*') and author.endswith('*') and \
                author.strip('*') in changeset.author:
                return True
            if author.startswith('*') and changeset.author.endswith(
                author.strip('*')):
                return True
            if author.endswith('*') and changeset.author.startswith(
                author.strip('*')):
                return True
            return changeset.author == author
        return True

    def get_changesets(self, repo, **options):
        if options.get('start_date'):
            options['start_date'] = parse_datetime(options['start_date'])
        if options.get('end_date'):
            options['end_date'] = parse_datetime(options['end_date'])
        changesets = repo.get_changesets(
            start=options.get('start'),
            end=options.get('end', options.get('main')),
            start_date=options.get('start_date'),
            end_date=options.get('end_date'),
            branch_name=options.get('all') and None or
                options.get('branch') or repo.workdir.get_branch(),
            reverse=not options.get('reversed', False),
        )
        try:
            limit = int(options.get('limit'))
        except (ValueError, TypeError):
            limit = None

        result = []
        count = 0
        for changeset in changesets:
            if self.show_changeset(changeset, **options):
                result.append(changeset)
                count += 1
                if count == limit:
                    break
        return result

    def handle_repo(self, repo, *args, **options):
        opts = copy.copy(options)
        if len(args) == 1:
            opts.update(parse_changesets(args[0]))
        elif len(args) > 1:
            raise CommandError("Wrong changeset ID(s) given")
        if options.get('limit') and not options['limit'].isdigit():
            raise CommandError("Limit must be a number")
        changesets = self.get_changesets(repo, **opts)
        self.iter_changesets(repo, changesets, **options)
        self.post_process(repo, **options)

    def iter_changesets(self, repo, changesets, **options):
        if self.show_progress_bar:
            progressbar = self.get_progressbar(len(changesets), **options)
            progressbar.render(0)
        else:
            progressbar = None
        i = 0
        for changeset in changesets:
            self.handle_changeset(changeset, **options)
            i += 1
            if progressbar:
                progressbar.render(i)

    def get_progressbar(self, total, **options):
        progressbar = ColoredProgressBar(total)
        progressbar.steps_label = 'Commit'
        progressbar.elements += ['eta', 'time']
        return progressbar

    def handle_changeset(self, changeset, **options):
        raise NotImplementedError()

    def post_process(self, repo, **options):
        pass


class SingleChangesetCommand(RepositoryCommand):

    min_args = 1

    option_list = RepositoryCommand.option_list + (
        make_option('-c', '--commit', action='store', dest='changeset_id',
            default=None, help='Use specific commit. By default we use HEAD/tip'),
    )

    def get_changeset(self, **options):
        cid = options.get('changeset_id', None)
        return self.repo.get_changeset(cid)

    def handle_repo(self, repo, *args, **options):
        if len(args) < self.min_args:
            raise CommandError("At least {min_args} arguments required".format(
                min_args=self.min_args))
        changeset = self.get_changeset(**options)
        for arg in args:
            self.handle_arg(changeset, arg, **options)

    def handle_arg(self, changeset, arg, **options):
        raise NotImplementedError()


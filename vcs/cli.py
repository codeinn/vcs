import os
import sys
import argparse
from vcs import get_repo
from vcs.exceptions import CommandError
from vcs.exceptions import VCSError
from vcs.utils.helpers import get_scm
from vcs.utils.paths import abspath


class BaseCommand(object):
    version = '%(prog)s 1.0'
    description = '...'
    allow_args = False
    args_dest = None

    def __call__(self, argv=None):
        if argv is None:
            argv = sys.argv[1:]
        parser = self.get_parser()
        self.setup_parser(parser)
        namespace = parser.parse_args(argv)
        self.execute(namespace)

    def get_parser(self):
        parser = argparse.ArgumentParser(version=self.version,
            description=self.description)
        return parser

    def setup_parser(self, parser):
        if self.allow_args:
            parser.add_argument(self.args_dest, nargs='+')
        

    def execute(self, namespace):
        self.args = namespace._get_args()
        self.options = dict(namespace._get_kwargs())
        self.handle(*self.args, **self.options)

    def handle(self, **options):
        raise NotImplementedError()


class RepositoryCommand(BaseCommand):

    def __init__(self, *args, **kwargs):
        if 'repo' not in kwargs:
            curdir = abspath(os.curdir)
            try:
                scm, path = get_scm(curdir, search_recursively=True)
            except VCSError:
                raise CommandError("Repository not found")
            kwargs['repo'] = get_repo(path, scm)
        self.repo = kwargs.pop('repo')
        super(RepositoryCommand, self).__init__(*args, **kwargs)

    def handle(self, **options):
        return self.handle_repo(self.repo, **options)

    def handle_repo(self, repo, **options):
        raise NotImplementedError()


def repository_command(func):
    class Command(RepositoryCommand):
        def handle_repo(self, repo, **options):
            return func(repo, **options)
    return Command()


class ChangesetCommand(RepositoryCommand):
    allow_args = True
    args_dest = 'changeset_id_list'

    def handle(self, **options):
        for changeset_id in options[self.args_dest]:
            changeset = self.repo.get_changeset(changeset_id)
            self.handle_changeset(changeset, **options)

    def handle_changeset(self, changeset, **options):
        raise NotImplementedError()


def changeset_command(func):
    class Command(ChangesetCommand):
        def handle_changeset(self, changeset, **options):
            return func(changeset, **options)
    return Command()


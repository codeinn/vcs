from vcs.cli import RepositoryCommand
from vcs.cli import make_option


class LogCommand(RepositoryCommand):
    option_list = RepositoryCommand.option_list + (
        make_option('-t', '--template', action='store', dest='template',
            default=u'{cs.date} | {cs.raw_id} | {cs.author}',
            help='Specify own template'),
    )

    def handle_repo(self, repo, *args, **options):
        template = options['template']
        for cs in repo:
            output = template.format(cs=cs)
            self.stdout.write(output)
            self.stdout.write(u'\n')


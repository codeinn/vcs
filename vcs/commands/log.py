from vcs.exceptions import CommandError
from vcs.cli import RepositoryCommand
from vcs.cli import make_option


class LogCommand(RepositoryCommand):
    args = '[<start-commit>..]<end-commit>'
    option_list = RepositoryCommand.option_list + (
        make_option('-t', '--template', action='store', dest='template',
            default=u'{cs.date} | {cs.raw_id} | {cs.author}',
            help='Specify own template'),
        make_option('-p', '--patch', action='store_true', dest='show_patches',
            default=False, help='Show patches'),
        make_option('-r', '--reversed', action='store_true', dest='reversed',
            default=False, help='Iterates in asceding order.'),
    )

    def get_last_commit(self, repo, cid=None):
        return repo.get_changeset(cid)
        

    def handle_repo(self, repo, *args, **options):
        if len(args) > 1:
            raise CommandError("Wrong number of arguments")
        cid = args and args[0] or None
        cs = self.get_last_commit(repo, cid)

        template = options['template']
        while cs:
            output = template.format(cs=cs)
            self.stdout.write(output)
            self.stdout.write(u'\n')
            cs = cs.parent


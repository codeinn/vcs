from vcs.nodes import FileNode
from vcs.cli import ChangesetCommand
from vcs.cli import make_option
from vcs.utils.diffs import get_udiff


class LogCommand(ChangesetCommand):
    TEMPLATE = u'{cs.raw_id} | {cs.date} | {cs.author} | {cs.message}'

    option_list = ChangesetCommand.option_list + (
        make_option('-t', '--template', action='store', dest='template',
            default=TEMPLATE,
            help=(
                'Specify own template. Default is: "{default_template}"'.format(
                default_template=TEMPLATE)),
        ),
        make_option('-p', '--patch', action='store_true', dest='show_patches',
            default=False, help='Show patches'),
    )

    def get_last_commit(self, repo, cid=None):
        if cid is None:
            cid = repo.branches[repo.workdir.get_branch()]
        return repo.get_changeset(cid)

    def get_template(self, **options):
            return options.get('template', self.TEMPLATE)

    def handle_changeset(self, changeset, **options):
        template = self.get_template(**options)
        output = template.format(cs=changeset)
        output = u'{output}\n'.format(output=output)
        self.stdout.write(output)

        if options.get('show_patches'):

            def show_diff(old_node, new_node):
                diff = get_udiff(old_node, new_node)
                self.stdout.write(u''.join(diff))

            for node in changeset.added:
                show_diff(FileNode('null', content=''), node)
            for node in changeset.changed:
                old_node = node.history[0].get_node(node.path)
                show_diff(old_node, node)
            for node in changeset.removed:
                old_node = changeset.parents[0].get_node(node.path)
                new_node = FileNode(node.path, content='')
                show_diff(old_node, new_node)


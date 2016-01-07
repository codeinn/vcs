import datetime

from vcs.backends.base import BaseChangeset
from vcs.utils.lazy import LazyProperty

class P4Changeset(BaseChangeset):
    """
    P4 changelist. Submitted CLs will be implemented first.

    **Attributes**

        ``repository``
            repository object within which changeset exists

        ``id``
            Changelist number (int)

        ``raw_id``
            same as id

        ``short_id``
            same as id

        ``revision``
            same as id

        ``files``
            list of ``FileNode`` (``Node`` with NodeKind.FILE) objects, TBD

        ``dirs``
            list of ``DirNode`` (``Node`` with NodeKind.DIR) objects, TBD

        ``nodes``
            combined list of ``Node`` objects, TBD

        ``author``
            author of the changeset, as unicode, TBD

        ``message``
            message of the changeset, as unicode

        ``parents``
            list of parent changesets, TBD

        ``last``
            ``True`` if this is last changeset in repository, ``False``
            otherwise; trying to access this attribute while there is no
            changesets would raise ``EmptyRepositoryError``, TBD

        ``date``
            datetime object representing date and time of the submit

        Added properties:

        ``raw_data``
            the raw dict returned by p4 lib or cmd
    """
    def __init__(self, changeset_dict):
        """

        :param changeset_dict: the raw dict returned by p4 cmd or lib
        :return:
        """
        self.revision = int(changeset_dict['change'])
        self.short_id = self.revision
        self.id = self.revision

        self.author = changeset_dict['user']
        self.message = changeset_dict['desc']

        self.raw_data = changeset_dict
        self.date = datetime.datetime.utcfromtimestamp(int(changeset_dict['time']))

    @LazyProperty
    def parents(self):
        """
        Returns list of parents changesets.
        """
        raise NotImplementedError

    @LazyProperty
    def children(self):
        """
        Returns list of children changesets.
        """
        raise NotImplementedError

    @LazyProperty
    def id(self):
        """
        Returns string identifying this changeset.
        """
        raise NotImplementedError

    @LazyProperty
    def raw_id(self):
        """
        Returns raw string identifying this changeset.
        """
        raise NotImplementedError

    @LazyProperty
    def short_id(self):
        """
        Returns shortened version of ``raw_id`` attribute, as string,
        identifying this changeset, useful for web representation.
        """
        raise NotImplementedError

    @LazyProperty
    def revision(self):
        """
        Returns integer identifying this changeset.

        """
        raise NotImplementedError

    @LazyProperty
    def committer(self):
        """
        Returns Committer for given commit
        """

        raise NotImplementedError

    @LazyProperty
    def committer_name(self):
        """
        Returns Author name for given commit
        """

        return author_name(self.committer)

    @LazyProperty
    def committer_email(self):
        """
        Returns Author email address for given commit
        """

        return author_email(self.committer)

    @LazyProperty
    def author(self):
        """
        Returns Author for given commit
        """

        raise NotImplementedError


    def get_file_mode(self, path):
        """
        Returns stat mode of the file at the given ``path``.
        """
        raise NotImplementedError

    def get_file_content(self, path):
        """
        Returns content of the file at the given ``path``.
        """
        raise NotImplementedError

    def get_file_size(self, path):
        """
        Returns size of the file at the given ``path``.
        """
        raise NotImplementedError

    def get_file_changeset(self, path):
        """
        Returns last commit of the file at the given ``path``.
        """
        raise NotImplementedError

    def get_file_history(self, path):
        """
        Returns history of file as reversed list of ``Changeset`` objects for
        which file at given ``path`` has been modified.
        """
        raise NotImplementedError

    def get_nodes(self, path):
        """
        Returns combined ``DirNode`` and ``FileNode`` objects list representing
        state of changeset at the given ``path``.

        :raises ``ChangesetError``: if node at the given ``path`` is not
          instance of ``DirNode``
        """
        raise NotImplementedError

    def get_node(self, path):
        """
        Returns ``Node`` object from the given ``path``.

        :raises ``NodeDoesNotExistError``: if there is no node at the given
          ``path``
        """
        raise NotImplementedError

    def fill_archive(self, stream=None, kind='tgz', prefix=None):
        """
        Fills up given stream.

        :param stream: file like object.
        :param kind: one of following: ``zip``, ``tar``, ``tgz``
            or ``tbz2``. Default: ``tgz``.
        :param prefix: name of root directory in archive.
            Default is repository name and changeset's raw_id joined with dash.

            repo-tip.<kind>
        """

        raise NotImplementedError

    def next(self, branch=None):
        """
        Returns next changeset from current, if branch is gives it will return
        next changeset belonging to this branch

        :param branch: show changesets within the given named branch
        """
        raise NotImplementedError

    def prev(self, branch=None):
        """
        Returns previous changeset from current, if branch is gives it will
        return previous changeset belonging to this branch

        :param branch: show changesets within the given named branch
        """
        raise NotImplementedError

    @LazyProperty
    def added(self):
        """
        Returns list of added ``FileNode`` objects.
        """
        raise NotImplementedError

    @LazyProperty
    def changed(self):
        """
        Returns list of modified ``FileNode`` objects.
        """
        raise NotImplementedError

    @LazyProperty
    def removed(self):
        """
        Returns list of removed ``FileNode`` objects.
        """
        raise NotImplementedError

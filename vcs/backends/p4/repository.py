import os

from vcs.backends.base import BaseRepository
from .common import SubprocessP4
import vcs.exceptions

class P4Repository(BaseRepository):
    """
    Base Repository for final backends

        ``repo``
            object from external api

        ``revisions``
            list of all available revisions' ids, in ascending order

        ``changesets``
            storage dict caching returned changesets

        ``path``
            absolute path to the repository

        ``branches``
            branches as list of changesets

        ``tags``
            tags as list of changesets
    """
    scm = 'p4'
    DEFAULT_BRANCH_NAME = None

    def __init__(self, repo_path, create=False, user=None, passwd=None, port=None, p4client=None):
        """
        Initializes repository. Raises RepositoryError if repository could
        not be find at the given ``repo_path`` or directory at ``repo_path``
        exists and ``create`` is set to True.

        :param repo_path: e.g. //depot/path/to/dir
        :param create=False: if set to True, would try to sync to your workspace
        :param p4user=None: if set, used for authorization. If none, taken from env var
        :param p4passwd=None: same as p4user
        :param p4port=None same as p4user
        :param p4client=None same as p4port
        """
        self.path = repo_path

        try:
            user = user or os.environ['P4USER']
            passwd = passwd or os.environ['P4PASSWD']
            port = port or os.environ['P4PORT']
        except KeyError:
            raise vcs.exceptions.RepositoryError('You have to specify user, password and port')

        client = p4client or os.environ.get('P4CLIENT')  # this one isn't mandatory for read operations

        self.repo_path = repo_path
        self.repo = SubprocessP4(user, passwd, port, client)

    def is_valid(self):
        """
        Validates repository.
        """
        raise NotImplementedError

    #==========================================================================
    # CHANGESETS
    #==========================================================================

    def get_changeset(self, revision=None):
        """
        Returns instance of ``Changeset`` class. If ``revision`` is None, most
        recent changeset is returned.

        :raises ``EmptyRepositoryError``: if there are no revisions
        """
        raise NotImplementedError

    def get_changesets(self, start=None, end=None, start_date=None,
                       end_date=None, branch_name=None, reverse=False):
        """
        Returns iterator of ``P4Changeset`` objects from start to end
        not inclusive This should behave just like a list, ie. end is not
        inclusive

        :param start: None or int
        :param end: None or int, should be bigger than start
        :param start_date:
        :param end_date:
        :param branch_name:
        :param reversed:
        """
        PAGE_SIZE = 1000

        result = self.repo.run(['changes', '-s', 'submitted', '-m', PAGE_SIZE, self.repo_path])

        # TODO do the previous command in cycle with modified start and end till you satisfy the start and end.
        # it is better to have multiple requests with 1k results, than one with millions of results

    def tag(self, name, user, revision=None, message=None, date=None, **opts):
        """
        Creates and returns a tag for the given ``revision``.

        :param name: name for new tag
        :param user: full username, i.e.: "Joe Doe <joe.doe@example.com>"
        :param revision: changeset id for which new tag would be created
        :param message: message of the tag's commit
        :param date: date of tag's commit

        :raises TagAlreadyExistError: if tag with same name already exists
        """
        raise NotImplementedError

    def remove_tag(self, name, user, message=None, date=None):
        """
        Removes tag with the given ``name``.

        :param name: name of the tag to be removed
        :param user: full username, i.e.: "Joe Doe <joe.doe@example.com>"
        :param message: message of the tag's removal commit
        :param date: date of tag's removal commit

        :raises TagDoesNotExistError: if tag with given name does not exists
        """
        raise NotImplementedError

    def get_diff(self, rev1, rev2, path=None, ignore_whitespace=False,
            context=3):
        """
        Returns (git like) *diff*, as plain text. Shows changes introduced by
        ``rev2`` since ``rev1``.

        :param rev1: Entry point from which diff is shown. Can be
          ``self.EMPTY_CHANGESET`` - in this case, patch showing all
          the changes since empty state of the repository until ``rev2``
        :param rev2: Until which revision changes should be shown.
        :param ignore_whitespace: If set to ``True``, would not show whitespace
          changes. Defaults to ``False``.
        :param context: How many lines before/after changed lines should be
          shown. Defaults to ``3``.
        """
        raise NotImplementedError

    # ========== #
    # COMMIT API #
    # ========== #

    @LazyProperty
    def in_memory_changeset(self):
        """
        Returns ``InMemoryChangeset`` object for this repository.
        """
        raise NotImplementedError

    def add(self, filenode, **kwargs):
        """
        Commit api function that will add given ``FileNode`` into this
        repository.

        :raises ``NodeAlreadyExistsError``: if there is a file with same path
          already in repository
        :raises ``NodeAlreadyAddedError``: if given node is already marked as
          *added*
        """
        raise NotImplementedError

    def remove(self, filenode, **kwargs):
        """
        Commit api function that will remove given ``FileNode`` into this
        repository.

        :raises ``EmptyRepositoryError``: if there are no changesets yet
        :raises ``NodeDoesNotExistError``: if there is no file with given path
        """
        raise NotImplementedError

    def commit(self, message, **kwargs):
        """
        Persists current changes made on this repository and returns newly
        created changeset.

        :raises ``NothingChangedError``: if no changes has been made
        """
        raise NotImplementedError

    def get_state(self):
        """
        Returns dictionary with ``added``, ``changed`` and ``removed`` lists
        containing ``FileNode`` objects.
        """
        raise NotImplementedError

    def get_config_value(self, section, name, config_file=None):
        """
        Returns configuration value for a given [``section``] and ``name``.

        :param section: Section we want to retrieve value from
        :param name: Name of configuration we want to retrieve
        :param config_file: A path to file which should be used to retrieve
          configuration from (might also be a list of file paths)
        """
        raise NotImplementedError

    def get_user_name(self, config_file=None):
        """
        Returns user's name from global configuration file.

        :param config_file: A path to file which should be used to retrieve
          configuration from (might also be a list of file paths)
        """
        raise NotImplementedError

    def get_user_email(self, config_file=None):
        """
        Returns user's email from global configuration file.

        :param config_file: A path to file which should be used to retrieve
          configuration from (might also be a list of file paths)
        """
        raise NotImplementedError

    # =========== #
    # WORKDIR API #
    # =========== #

    @LazyProperty
    def workdir(self):
        """
        Returns ``Workdir`` instance for this repository.
        """
        raise NotImplementedError
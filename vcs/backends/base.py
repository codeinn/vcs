#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2010 Marcin Kuzminski,Lukasz Balcerzak.  All rights reserved.
#
"""
Created on Apr 8, 2010

:author: marcink,lukaszb
"""
from itertools import chain

from vcs.utils.lazy import LazyProperty
from vcs.exceptions import ChangesetError
from vcs.exceptions import RepositoryError
from vcs.exceptions import NodeAlreadyAddedError
from vcs.exceptions import NodeAlreadyExistsError
from vcs.exceptions import NodeAlreadyRemovedError
from vcs.exceptions import NodeDoesNotExistError
from vcs.exceptions import NodeNotChangedError


class BaseRepository(object):
    """
    Base Repository for final backends

    :attribute: ``repo`` object from external api
    :attribute: revisions: list of all available revisions' ids, in ascending
      order
    :attribute: changesets: storage dict caching returned changesets
    :attribute: path: absolute local path to the repository
    :attribute: branches: branches as list of changesets
    :attribute: tags: tags as list of changesets
    """

    def __init__(self, repo_path, create=False, **kwargs):
        """
        Initializes repository. Raises RepositoryError if repository could
        not be find at the given ``repo_path``.

        :param repo_path: local path of the repository
        :param create=False: if set to True, would try to craete repository if
           it does not exist rather than raising exception
        """
        raise NotImplementedError

    def __str__(self):
        return '<%s at %s>' % (self.__class__.__name__, self.path)

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return self.count()

    @LazyProperty
    def name(self):
        """ This is name attribute """
        raise NotImplementedError

    @LazyProperty
    def owner(self):
        raise NotImplementedError

    @LazyProperty
    def description(self):
        raise NotImplementedError

    def is_valid(self):
        """
        Validates repository.
        """
        raise NotImplementedError

    def get_last_change(self):
        self.get_changesets(limit=1)

    #===========================================================================
    # CHANGESETS
    #===========================================================================

    def get_changeset(self, revision=None):
        """
        Returns instance of ``Changeset`` class. If ``revision`` is None, most
        recenent changeset is returned.
        """
        raise NotImplementedError

    def __iter__(self):
        """
        Allows Repository objects to be iterated.

        *Requires* implementation of ``__getitem__`` method.
        """
        for revision in reversed(self.revisions):
            yield self.get_changeset(revision)

    def get_changesets(self, limit=10, offset=None):
        """
        Return last n number of ``Changeset`` objects specified by limit
        attribute if None is given whole list of revisions is returned

        @param limit: int limit or None
        @param offset: int offset
        """
        raise NotImplementedError

    def __getslice__(self, i, j):
        """
        Convenient wrapper for ``get_changesets`` method. Those two are same:

        self[2:5] == self.get_changesets(offset=2, limit=3)
        """
        return self.get_changesets(offset=i, limit=j - i)

    def count(self):
        return len(self.revisions)

    def request(self, path, revision=None):
        chset = self.get_changeset(revision)
        node = chset.get_node(path)
        return node

    def walk(self, topurl='', revision=None):
        chset = self.get_changeset(revision)
        return chset.walk(topurl)

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
        repository. If there is a file with same path already in repository,
        ``NodeAlreadyExistsError`` is raised.
        """
        raise NotImplementedError

    def remove(self, filenode, **kwargs):
        """
        Commit api function that will remove given ``FileNode`` into this
        repository. If there is no file with given path,
        ``NodeDoesNotExistError`` is raised.
        """
        raise NotImplementedError

    def commit(self, message, **kwargs):
        """
        Persists current changes made on this repository and returns newly
        created changeset. If no changed has been made, ``NothingChangedError``
        is raised.
        """
        raise NotImplementedError

    def get_state(self):
        """
        Returns dictionary with ``added``, ``changed`` and ``removed`` lists
        containing ``FileNode`` objects.
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


class BaseChangeset(object):
    """
    Each backend should implement it's changeset representation.

    :attribute: repository: repository object within which changeset exists
    :attribute: id: may be raw_id or i.e. for mercurial's tip just ``tip``
    :attribute: raw_id: raw changeset representation (i.e. full 40 length sha
      for git backend) as string
    :attribute: short_id: shortened (if needed) version of raw_id; it would be
      simple shortcut for ``raw_id[:12]``
    :attribute: revision: revision number as integer
    :attribute: files: list of ``Node`` objects with NodeKind.FILE
    :attribute: dirs: list of ``Node`` objects with NodeKind.DIR
    :attribute: nodes: combined list of ``Node`` objects
    :attribute: author: author of the changeset
    :attribute: message: message of the changeset
    :attribute: size: integer size in bytes
    :attribute: last: True if this is last changeset in repository, False
      otherwise; ``ChangesetError`` is raised if not related with repository
      object
    """

    def __str__(self):
        return '<%s at %s:%s>' % (self.__class__.__name__, self.revision,
            self.raw_id)

    def __repr__(self):
        return self.__str__()

    def __unicode__(self):
        return u'%s:%s' % (self.revision, self.short_id)

    @LazyProperty
    def last(self):
        """
        Returns True if this is last changeset in repository, False otherwise.
        Note that ChangesetError would be raised if object is not related with
        repository object.
        """
        if self.repository is None:
            raise ChangesetError("Cannot check if it's most recent revision")
        return self.revision == self.repository.revisions[-1]

    @LazyProperty
    def parents(self):
        """
        Returns list of parents changesets.
        """
        raise NotImplementedError

    @LazyProperty
    def id(self):
        """
        Returns string identifing this changeset.
        """
        raise NotImplementedError

    @LazyProperty
    def raw_id(self):
        """
        Returns raw string identifing this changeset.
        """
        raise NotImplementedError

    @LazyProperty
    def short_id(self):
        """
        Returns shortened version of ``raw_id`` attribute, as string,
        identifing this changeset, useful for web representation.
        """
        raise NotImplementedError

    @LazyProperty
    def revision(self):
        """
        Returns integer identifing this changeset.

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

    def get_file_message(self, path):
        """
        Returns message of the last commit related to file at the given
        ``path``.
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
        state of changeset at the given ``path``. If node at the given ``path``
        is not instance of ``DirNode``, ChangesetError would be raised.
        """
        raise NotImplementedError

    def get_node(self, path):
        """
        Returns ``Node`` object from the given ``path``. If there is no node at
        the given ``path``, ``ChangesetError`` would be raised.
        """
        raise NotImplementedError

    @LazyProperty
    def root(self):
        """
        Returns ``RootNode`` object for this changeset.
        """
        return self.get_node('')

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

    def walk(self, topurl=''):
        """
        Similar to os.walk method. Insted of filesystem it walks through
        changeset starting at given ``topurl``.  Returns generator of tuples
        (topnode, dirnodes, filenodes).
        """
        topnode = self.get_node(topurl)
        yield (topnode, topnode.dirs, topnode.files)
        for dirnode in topnode.dirs:
            for tup in self.walk(dirnode.path):
                yield tup


class BaseWorkdir(object):
    """
    Working directory representation of single repository.

    :attribute: repository: repository object of working directory
    """

    def __init__(self, repository):
        self.repository = repository

    def get_added(self):
        """
        Returns list of ``FileNode`` objects marked as *new* in working
        directory.
        """
        raise NotImplementedError

    def get_changed(self):
        """
        Returns list of ``FileNode`` objects *changed* in working directory.
        """
        raise NotImplementedError

    def get_removed(self):
        """
        Returns list of ``RemovedFileNode`` objects marked as *removed* in
        working directory.
        """
        raise NotImplementedError

    def get_untracked(self):
        """
        Returns list of ``FileNode`` objects which are present within working
        directory however are not tracked by repository.
        """
        raise NotImplementedError

    def commit(self, message, **kwargs):
        """
        Commits local (from working directory) changes and returns newly created
        ``Changeset``. Updates repository's ``revisions`` list.

        :raises ``CommitError``: if any error occurs while committing
        """
        raise NotImplementedError

    def update(self, revision=None):
        """
        Fetches content of the given revision and populates it within working
        directory.
        """
        raise NotImplementedError


class BaseInMemoryChangeset(object):
    """
    Represents differences between repository's state (most recent head) and
    changes made *in place*.

    :attribute: repository: repository object of working directory
    :attribute: added: list of new ``FileNode`` objects going to be committed
    :attribute: changed: list of changed ``FileNode`` objects going to be
      committed
    :attribute: removed: list of ``RemovedFileNode`` objects marked to be
      removed
    """

    def __init__(self, repository):
        self.repository = repository
        self.added = []
        self.changed = []
        self.removed = []

    def add(self, *filenodes):
        """
        Marks given ``FileNode`` objects as *to be committed*.

        :raises ``NodeAlreadyExistsError``: if node with same path exists at
          latest changeset
        :raises ``NodeAlreadyAddedError``: if node with same path is already
          marked as *new*
        """
        try:
            tip = self.repository.get_changeset()
        except RepositoryError:
            tip = None
        for node in filenodes:
            if node.path in (n.path for n in self.added):
                raise NodeAlreadyAddedError("Such FileNode %s is already "
                    "marked for addition" % node.path)
            if tip:
                try:
                    tip.get_node(node.path)
                except ChangesetError:
                    pass
                else:
                    raise NodeAlreadyExistsError(str(node.path))
            self.added.append(node)

    def change(self, *filenodes):
        """
        Marks given ``FileNode`` objects to be *changed* in next commit.

        :raises ``ChangesetError``: if node doesn't exist in latest changeset or
          node with same path is already marked as *changed*.
        :raises ``RepositoryError``: if there are no changesets yet
        """
        tip = self.repository.get_changeset()
        for node in filenodes:
            if node.path in (n.path for n in self.changed):
                raise NodeAlreadyExistsError("Such FileNode %s is already "
                    "marked as changed" % node.path)
            try:
                old = tip.get_node(node.path)
                if old.content == node.content:
                    raise NodeNotChangedError(str(node.path))
            except ChangesetError:
                raise NodeDoesNotExistError(str(node.path))
            self.changed.append(node)

    def remove(self, *filenodes):
        """
        Marks given ``FileNode`` (or ``RemovedFileNode``) objects to be
        *removed* in next commit. If ``FileNode`` doesn't exists

        :raises ``ChangesetError``: if node does not exist in latest changeset
        :raises ``RepositoryError``: if there are no changesets yet
        :raises ``NodeAlreadyRemovedError``: if node has been already marked to
          be *removed*
        """
        tip = self.repository.get_changeset()
        for node in filenodes:
            try:
                tip.get_node(node.path)
            except ChangesetError:
                raise NodeDoesNotExistError(str(node.path))
            if node.path in (n.path for n in self.removed):
                raise NodeAlreadyRemovedError("Node is already marked to "
                    "for removal %s" % node.path)
            # We only mark node as *removed* - real removal is done by
            # commit method
            self.removed.append(node)

    def reset(self):
        """
        Resets this instance to initial state (cleans ``added``, ``changed`` and
        ``removed`` lists).
        """
        self.added = []
        self.changed = []
        self.removed = []

    def get_ipaths(self):
        """
        Returns generator of paths from nodes marked as added, changed or
        removed.
        """
        for node in chain(self.added, self.changed, self.removed):
            yield node.path

    def get_paths(self):
        """
        Returns list of paths from nodes marked as added, changed or removed.
        """
        return list(self.get_ipaths())

    def commit(self, message, **kwargs):
        """
        Commits local (from working directory) changes and returns newly created
        ``Changeset``. Updates repository's ``revisions`` list.

        :raises ``CommitError``: if any error occurs while committing
        """
        raise NotImplementedError


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
from vcs.exceptions import EmptyRepositoryError
from vcs.exceptions import ChangesetError
from vcs.exceptions import NodeAlreadyAddedError
from vcs.exceptions import NodeAlreadyExistsError
from vcs.exceptions import NodeAlreadyRemovedError
from vcs.exceptions import NodeAlreadyChangedError
from vcs.exceptions import NodeDoesNotExistError
from vcs.exceptions import NodeNotChangedError

from warnings import warn

class BaseRepository(object):
    """
    Base Repository for final backends

    **Attributes**

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

    def __init__(self, repo_path, create=False, **kwargs):
        """
        Initializes repository. Raises RepositoryError if repository could
        not be find at the given ``repo_path`` or directory at ``repo_path``
        exists and ``create`` is set to True.

        :param repo_path: local path of the repository
        :param create=False: if set to True, would try to craete repository.
        :param src_url=None: if set, should be proper url from which repository
          would be cloned; requires ``create`` parameter to be set to True -
          raises RepositoryError if src_url is set and create evaluates to False
        """
        raise NotImplementedError

    def __str__(self):
        return '<%s at %s>' % (self.__class__.__name__, self.path)

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return self.count()
    
    @LazyProperty
    def alias(self):
        from vcs.backends import BACKENDS
        for k, v in BACKENDS.items():
            if v.split('.')[-1] == str(self.__class__.__name__):
                return k
    
    @LazyProperty
    def name(self):
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

        :raises ``EmptyRepositoryError``: if there are no revisions
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

        :param: ``limit``: int limit or None
        :param: ``offset``: int offset
        """
        raise NotImplementedError

    def __getslice__(self, i, j):
        """
        Convenient wrapper for ``get_changesets`` method. Those two are same::

            >>> repo[2:5] == repo.get_changesets(offset=2, limit=3)

        """
        return self.get_changesets(offset=i, limit=j - i)

    def count(self):
        return len(self.revisions)

    def request(self, path, revision=None):
        warn("request method is deprecated and will be removed in version 1.0."
             " Please, use get_changeset to retrieve revision and then get_node"
             " method instead.", DeprecationWarning)
        chset = self.get_changeset(revision)
        node = chset.get_node(path)
        return node

    def walk(self, topurl='', revision=None):
        warn("walk method is deprecated and will be removed in version 1.0. "
             "Please, use get_changeset to retrieve revision and then walk "
             "method instead.", DeprecationWarning)
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

    **Attributes**

        ``repository``
            repository object within which changeset exists

        ``id``
            may be ``raw_id`` or i.e. for mercurial's tip just ``tip``

        ``raw_id``
            raw changeset representation (i.e. full 40 length sha for git
            backend)

        ``short_id``
            shortened (if apply) version of ``raw_id``; it would be simple
            shortcut for ``raw_id[:12]`` for git/mercurial backends or same
            as ``raw_id`` for subversion

        ``revision``
            revision number as integer

        ``files``
            list of ``FileNode`` (``Node`` with NodeKind.FILE) objects

        ``dirs``
            list of ``DirNode`` (``Node`` with NodeKind.DIR) objects

        ``nodes``
            combined list of ``Node`` objects

        ``author``
            author of the changeset, as unicode

        ``message``
            message of the changeset, as unicode

        ``parents``
            list of parent changesets

        ``last``
            ``True`` if this is last changeset in repository, ``False``
            otherwise; trying to access this attribute while there is no
            changesets would raise ``EmptyRepositoryError``
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

    def get_status(self):
        """
        Returns dict with ``added``, ``changed``, ``removed`` and ``untracked``
        lists.
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

    **Attributes**

        ``repository``
            repository object for this in-memory-changeset

        ``added``
            list of ``FileNode`` objects marked as *added*

        ``changed``
            list of ``FileNode`` objects marked as *changed*

        ``removed``
            list of ``FileNode`` or ``RemovedFileNode`` objects marked to be
            *removed*

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
          marked as *added*
        """
        # Check if not already marked as *added* first
        for node in filenodes:
            if node.path in (n.path for n in self.added):
                raise NodeAlreadyAddedError("Such FileNode %s is already "
                    "marked for addition" % node.path)
        try:
            tip = self.repository.get_changeset()
        except EmptyRepositoryError:
            tip = None
        for node in filenodes:
            if tip:
                try:
                    tip.get_node(node.path)
                except NodeDoesNotExistError:
                    pass
                else:
                    raise NodeAlreadyExistsError("Node at %s exists at "
                        "latest changeset" % node.path)
            self.added.append(node)

    def change(self, *filenodes):
        """
        Marks given ``FileNode`` objects to be *changed* in next commit.

        :raises ``EmptyRepositoryError``: if there are no changesets yet
        :raises ``NodeAlreadyExistsError``: if node with same path is already
          marked to be *changed*
        :raises ``NodeAlreadyRemovedError``: if node with same path is already
          marked to be *removed*
        :raises ``NodeDoesNotExistError``: if node doesn't exist in latest
          changeset
        :raises ``NodeNotChangedError``: if node hasn't really be changed
        """
        for node in filenodes:
            if node.path in (n.path for n in self.removed):
                raise NodeAlreadyRemovedError("Node at %s is already marked "
                    "as removed" % node.path)
        try:
            tip = self.repository.get_changeset()
        except EmptyRepositoryError:
            raise EmptyRepositoryError("Nothing to change - try to *add* new "
                "nodes rather than changing them")
        for node in filenodes:
            if node.path in (n.path for n in self.changed):
                raise NodeAlreadyChangedError("Node at '%s' is already "
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
        *removed* in next commit.

        :raises ``EmptyRepositoryError``: if there are no changesets yet
        :raises ``NodeDoesNotExistError``: if node does not exist in latest
          changeset
        :raises ``NodeAlreadyRemovedError``: if node has been already marked to
          be *removed*
        :raises ``NodeAlreadyChangedError``: if node has been already marked to
          be *changed*
        """
        tip = self.repository.get_changeset()
        for node in filenodes:
            try:
                tip.get_node(node.path)
            except ChangesetError:
                raise NodeDoesNotExistError(str(node.path))
            if node.path in (n.path for n in self.removed):
                raise NodeAlreadyRemovedError("Node is already marked to "
                    "for removal at %s" % node.path)
            if node.path in (n.path for n in self.changed):
                raise NodeAlreadyChangedError("Node is already marked to "
                    "be changed at %s" % node.path)
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


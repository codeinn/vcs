#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2010 Marcin Kuzminski,Lukasz Balcerzak.  All rights reserved.
#
"""
Created on Apr 8, 2010

@author: marcink,lukaszb
"""
from vcs.utils.lazy import LazyProperty
from vcs.exceptions import ChangesetError

class BaseRepository(object):
    """
    Base Repository for final backends

    :attribute: ``repo`` object from external api
    :attribute: revisions: list of all available revisions' ids
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
        for revision in self.revisions:
            yield self.get_changeset(revision)

    def get_changesets(self, since=None, limit=None):
        """
        Returns all commits since given ``since`` parameter. If ``since`` is
        None it returns all commits limited by ``limit``, or all commits if
        ``limit`` is None.

        @param since: datetime
        @param limit: integer value for limit
        """
        raise NotImplementedError

    def __getslice__(self, i, j):
        """
        Convenient wrapper for ``get_changesets`` method. Those two are same:

        self[2:5] == self.get_changesets(offset=2, limit=3)
        """
        return self.get_changesets(offset=i, limit=j-i)

    def count(self):
        return len(self.revisions)

    def request(self, path, revision=None):
        chset = self.get_changeset(revision)
        node = chset.get_node(path)
        return node

    #===========================================================================
    # TAGS
    #===========================================================================

    def get_tags(self, since='', limit=10):
        raise NotImplementedError

    def get_tag_by_name(self, tag_name):
        raise NotImplementedError

    def get_tag(self, tag_id):
        raise NotImplementedError

    #===========================================================================
    # BRANCHES
    #===========================================================================

    def get_branches(self, since='', limit=10):
        raise NotImplementedError

    def get_branch_by_name(self, branch_name):
        raise NotImplementedError

    def get_branch(self, branch_id):
        raise NotImplementedError

    def get_files(self, limit):
        raise NotImplementedError

class BaseChangeset(object):
    """
    Each backend should implement it's changeset representation.

    :attribute: revision: revision number as integer
    :attribute: files: list of ``Node`` objects with NodeKind.FILE
    :attribute: dirs: list of ``Node`` objects with NodeKind.DIR
    :attribute: nodes: combined list of ``Node`` objects
    :attribute: author: author of the changeset
    :attribute: message: message of the changeset
    :attribute: size: integer size in bytes
    :attribute: branch: title of the branch, as string
    :attribute: tags: list of tags, as list of strings
    """

    def __str__(self):
        return '<%s at %s>' % (self.__class__.__name__, self.revision)

    def __repr__(self):
        return self.__str__()

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
        Returns raw string identifing this changeset, useful for web
        representation.
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


#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2010 Marcin Kuzminski,Lukasz Balcerzak.  All rights reserved.
#
"""
Created on Apr 8, 2010

@author: marcink,lukaszb
"""

class BaseRepository(object):
    """
    Base Repository for final backends
    """

    def get_owner(self):
        raise NotImplementedError

    def get_last_change(self):
        self.get_commits(limit=1)

    def get_description(self):
        raise NotImplementedError

    def get_name(self):
        raise NotImplementedError

    def list_directory(self, path, revision=None):
        """
        Returns a list of files in a directory at a given
        revision, or HEAD if revision is None.
        """
        raise NotImplementedError

    #===========================================================================
    # CHANGESETS
    #===========================================================================
    def get_changesets(self, since=None, limit=None):
        """
        Returns all commits since given ``since`` parameter. If ``since`` is
        None it returns all commits limited by ``limit``, or all commits if
        ``limit`` is None.

        @param since: datetime
        @param limit: integer value for limit
        """
        raise NotImplementedError

    def get_commit_by_id(self, commit_id):
        raise NotImplementedError

    #===========================================================================
    # TAGS
    #===========================================================================
    def get_tags(self, since, limit):
        raise NotImplementedError

    def get_tag_by_name(self, tag_name):
        raise NotImplementedError

    def get_tag_by_id(self, tag_id):
        raise NotImplementedError

    #===========================================================================
    # BRANCHES
    #===========================================================================
    def get_branches(self, since, limit):
        raise NotImplementedError

    def get_branch_by_name(self, branch_name):
        raise NotImplementedError

    def get_branch_by_id(self, branch_id):
        raise NotImplementedError

    def get_files(self, limit):
        raise NotImplementedError

    def create_repository(self, repo_path, repo_name):
        """
        Create a repository on filesystem or throws an exception on fail
        """
        raise NotImplementedError

    def is_valid_repository(self, repo_path):
        """
        Check if there is a valid repository in given location
        """
        raise NotImplementedError

    def can_create_repository(self):
        """
        Checks if is possible to create repository by checking the permissions
        and path
        """
        raise NotImplementedError

class BaseChangeset(object):
    """
    Each backend should implement it's changeset representation.

    @attr revision: revision number as integer
    @attr files: list of ``Node`` objects with NodeKind.FILE
    @attr dirs: list of ``Node`` objects with NodeKind.DIR
    @attr nodes: combined list of ``Node`` objects
    @attr author: author of the changeset
    @attr message: message of the changeset
    @attr size: integer size in bytes
    """

    def get_nodes(self):
        """
        Returns combined list of files and directories ``Node`` objects.
        """
        raise NotImplementedError

    def get_files(self):
        """
        Returns list of ``Node`` objects with NodeKind.FILE.
        """
        raise NotImplementedError

    def get_dirs(self):
        """
        Returns list of ``Node`` objects with NodeKind.DIR.
        """
        raise NotImplementedError

    def get_kind(self, path):
        """
        Returns ``NodeKind.FILE`` if node at given path is a file,
        ``NodeKind.DIR`` if is a dir or raises ``ChangesetError`` if there is
        no node at the given ``path``.
        """
        raise NotImplementedError


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
    
    def get_changesets(self, since, limit):
        raise NotImplementedError
    
    #===========================================================================
    # COMMITS                
    #===========================================================================
    def get_commits(self, since=None, limit=None):     
        """ 
        Returns all commits since since. If since is None it returns all commits
        limited by limit, or all commits if limit is None
        @param since: datetime
        @param limit:Integer value for limit
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
    
    def get_branches_by_name(self, branch_name):
        raise NotImplementedError
    
    def get_branches_by_id(self, branch_id):
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
        Checks if is possible to create repository by checking the permissions and path
        """
        raise NotImplementedError
   

#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2010 Marcin Kuzminski,Lukasz Balcerzak.  All rights reserved.
#
'''
Created on Apr 8, 2010

@author: marcink,lukaszb
'''

class BaseRepository(object):
    '''
    Base Repository for final backends
    '''
        
    def get_owner(self):
        raise NotImplementedError
    
    def get_last_change(self):
        raise NotImplementedError
    
    def get_description(self):
        raise NotImplementedError
    
    def get_name(self):
        raise NotImplementedError
    
            
    def get_commits(self, since=None, limit=None):     
        '''
        Returns all commits since since. If since is None it returns all commits
        limited by limit, or all commits if limit is None
        @param since: datetime
        @param limit:Integer value for limit
        '''
        raise NotImplementedError
    
    def get_changesets(self, since, limit):
        raise NotImplementedError




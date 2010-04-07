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


    def __init__(self):
        '''
        Constructor
        '''
        
    def get_commits(self, since, limit):
        raise NotImplementedError
    
    def get_changesets(self, since, limit):
        raise NotImplementedError

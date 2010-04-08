#
# Copyright (c) 2010 Marcin Kuzminski,Lukasz Balcerzak.  All rights reserved.
#
"""
Created on Apr 8, 2010

@author: marcink,lukaszb
"""

class VCSError(Exception):
    pass

class RepositoryError(VCSError):
    pass

class ChangesetError(VCSError):
    pass


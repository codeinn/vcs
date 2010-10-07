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

class EmptyRepositoryError(RepositoryError):
    pass

class ChangesetError(RepositoryError):
    pass

class ChangesetDoesNotExistError(ChangesetError):
    pass

class CommitError(RepositoryError):
    pass

class NothingChangedError(CommitError):
    pass

class NodeAlreadyExistsError(CommitError):
    pass

class NodeAlreadyChangedError(CommitError):
    pass

class NodeDoesNotExistError(CommitError):
    pass

class NodeNotChangedError(CommitError):
    pass

class NodeAlreadyAddedError(CommitError):
    pass

class NodeAlreadyRemovedError(CommitError):
    pass

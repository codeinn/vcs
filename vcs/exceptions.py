# -*- coding: utf-8 -*-


class VCSError(Exception):
    pass


class RepositoryError(VCSError):
    pass


class EmptyRepositoryError(RepositoryError):
    pass


class TagAlreadyExistError(RepositoryError):
    pass


class TagDoesNotExistError(RepositoryError):
    pass


class BranchAlreadyExistError(RepositoryError):
    pass


class BranchDoesNotExistError(RepositoryError):
    pass


class ChangesetError(RepositoryError):
    pass


class ChangesetDoesNotExistError(ChangesetError):
    pass


class CommitError(RepositoryError):
    pass


class NothingChangedError(CommitError):
    pass


class NodeError(VCSError):
    pass


class RemovedFileNodeError(NodeError):
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


class ImproperArchiveTypeError(VCSError):
    pass


class CommandError(VCSError):
    pass

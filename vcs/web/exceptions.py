"""
Web specific exception classes, derived from ``vcs.exceptions.VCSError``.
"""
from vcs.exceptions import VCSError

class RequestError(VCSError):
    pass


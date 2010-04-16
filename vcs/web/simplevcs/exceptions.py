"""
``simplevcs`` specific exception classes are defined here. All are derived from
``vcs.exceptions.VCSError`` or it's subclasses.
"""

from vcs.exceptions import VCSError
from vcs.web.exceptions import RequestError

class NotMercurialRequest(RequestError):
    pass


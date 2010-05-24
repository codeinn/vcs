"""
Various Version Control System management abstraction layer for Python.
"""

VERSION = (0, 1, 2, 'beta')

__version__ = '.'.join((str(each) for each in VERSION[:4]))

__all__ = [
    'get_version', 'get_repo', 'get_backend', 'BACKENDS',
    'VCSError', 'RepositoryError', 'ChangesetError']

from vcs.backends import get_repo, get_backend, BACKENDS
from vcs.exceptions import VCSError, RepositoryError, ChangesetError

def get_version():
    """
    Returns shorter version (digit parts only) as string.
    """
    return '.'.join((str(each) for each in VERSION[:3]))

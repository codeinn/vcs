"""
Various Version Control System management abstraction layer for Python.
"""

VERSION = (0, 0, 1, 'alpha')

__version__ = '.'.join((str(each) for each in VERSION[:4]))

from vcs.backends import get_repo
from vcs.exceptions import VCSError


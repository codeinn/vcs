"""
Implements perforce backend. Uses command p4 -G to get all the info.

Perforce streams not supported yet. Helix dvcs not supported yet.

Used with server and client 2015.1. Older or newer versions may not work.
"""

from .repository import P4Repository
from .changeset import P4Changeset



__all__ = [
    'P4Repository', 'P4Changeset'
]

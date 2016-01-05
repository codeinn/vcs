"""
Implements perforce backend. Uses command p4 -G to get all the info.

Perforce streams not supported yet. Helix dvcs not supported yet.
"""

from .repository import P4Repository
from .changeset import P4Changeset



__all__ = [
    'P4Repository', 'P4Changeset'
]

""" backends module"""
from pprint import pformat
from vcs.exceptions import VCSError
from vcs.utils.imports import import_class

REPOSITORY_BACKENDS = {
    'hg': 'vcs.backends.hg.MercurialRepository',
}

def get_repo(alias):
    """
    Returns ``Repository`` class identified by the given alias or raises
    VCSError if alias is not recognized or backend class cannot be imported.
    """
    if alias not in REPOSITORY_BACKENDS:
        raise VCSError("Given alias '%s' is not recognized! Allowed aliases:\n"
            "%s" % (alias, pformat(REPOSITORY_BACKENDS.keys())))
    backend_path = REPOSITORY_BACKENDS[alias]
    klass = import_class(backend_path)
    return klass


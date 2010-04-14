from pprint import pformat
from vcs.exceptions import VCSError
from vcs.utils.imports import import_class

BACKENDS = {
    'hg': 'vcs.backends.hg.MercurialRepository',
}

def get_repo(alias, path):
    """
    Returns ``Repository`` object of type linked with given ``alias`` at
    the specified ``path``.
    """
    backend = get_backend(alias)
    repo = backend(path)
    return repo

def get_backend(alias):
    """
    Returns ``Repository`` class identified by the given alias or raises
    VCSError if alias is not recognized or backend class cannot be imported.
    """
    if alias not in BACKENDS:
        raise VCSError("Given alias '%s' is not recognized! Allowed aliases:\n"
            "%s" % (alias, pformat(BACKENDS.keys())))
    backend_path = BACKENDS[alias]
    klass = import_class(backend_path)
    return klass


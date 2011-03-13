# -*- coding: utf-8 -*-
"""
    vcs.backends
    ~~~~~~~~~~~~

    Main package for scm backends

    :created_on: Apr 8, 2010
    :copyright: (c) 2010-2011 by Marcin Kuzminski, Lukasz Balcerzak.
"""

from pprint import pformat
from vcs.exceptions import VCSError
from vcs.utils.helpers import get_scm
from vcs.utils.paths import abspath
from vcs.utils.imports import import_class

BACKENDS = {
    'hg': 'vcs.backends.hg.MercurialRepository',
    'git': 'vcs.backends.git.GitRepository',
}

ARCHIVE_SPECS = {
    'tar': ('application/x-tar', '.tar'),
    'tbz2': ('application/x-bzip2', '.tar.bz2'),
    'tgz': ('application/x-gzip', '.tar.gz'),
    'zip': ('application/zip', '.zip'),
}


def get_repo(path, alias=None, create=False):
    """
    Returns ``Repository`` object of type linked with given ``alias`` at
    the specified ``path``. If ``alias`` is not given it will try to guess it
    using get_scm method
    """
    path = abspath(path)
    if alias is None:
        alias = get_scm(path)[0]

    backend = get_backend(alias)
    repo = backend(path, create=create)
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


def get_supported_backends():
    """
    Returns list of aliases of supported backends.
    """
    return BACKENDS.keys()

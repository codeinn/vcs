import os

abspath = lambda *p: os.path.abspath(os.path.join(*p))

VCSRC_PATH = os.environ.get('VCSRC_PATH', abspath(os.getenv('HOME'), '.vcsrc'))

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


import os
import tempfile

abspath = lambda * p: os.path.abspath(os.path.join(*p))

VCSRC_PATH = os.environ.get('VCSRC_PATH')

if not VCSRC_PATH:
    HOME_ = os.getenv('HOME',os.getenv('USERPROFILE',tempfile.gettempdir()))

VCSRC_PATH = VCSRC_PATH or abspath(HOME_, '.vcsrc')
if os.path.isdir(VCSRC_PATH):
    VCSRC_PATH = os.path.join(VCSRC_PATH, '__init__.py')

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

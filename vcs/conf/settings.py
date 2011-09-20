import os

abspath = lambda *p: os.path.abspath(os.path.join(*p))

VCSRC_PATH = os.environ.get('VCSRC_PATH', abspath(os.getenv('HOME'), '.vcsrc'))


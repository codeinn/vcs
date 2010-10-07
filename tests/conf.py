"""
Unit tests configuration module for vcs.
"""
import os
import time
import hashlib
import tempfile
import datetime

from utils import get_normalized_path

__all__ = (
    'TEST_HG_REPO', 'TEST_GIT_REPO', 'HG_REMOTE_REPO', 'GIT_REMOTE_REPO',
    'SCM_TESTS',
)

SCM_TESTS = ['hg', 'git']
uniq_suffix = str(int(time.mktime(datetime.datetime.now().timetuple())))
TEST_GIT_REPO = os.environ.get('VCS_TEST_GIT_REPO', '/tmp/vcs-git')
GIT_REMOTE_REPO = 'git@github.com:lukaszb/vcs.git'
HG_REMOTE_REPO = 'http://bitbucket.org/marcinkuzminski/vcs'

TEST_HG_REPO = os.environ.get('VCS_TEST_HG_REPO',
                              '/tmp/vcs%s' % uniq_suffix)
TEST_HG_REPO_CLONE = os.environ.get('VCS_TEST_HG_REPO_CLONE',
                                    '/tmp/vcshgclone%s' % uniq_suffix)
TEST_HG_REPO_PULL = os.environ.get('VCS_TEST_HG_REPO_PULL',
                                   '/tmp/vcshgpull%s' % uniq_suffix)

TEST_DIR = tempfile.gettempdir()
TEST_REPO_PREFIX = 'vcs-test'

def get_new_dir(title):
    """
    Returns always new directory path.
    """
    name = TEST_REPO_PREFIX
    if title:
        name = '-'.join((name, title))
    hex = hashlib.sha1(str(time.time())).hexdigest()
    name = '-'.join((name, hex))
    path = os.path.join(TEST_DIR, name)
    return get_normalized_path(path)


PACKAGE_DIR = os.path.abspath(os.path.join(
    os.path.dirname(__file__), '..'))


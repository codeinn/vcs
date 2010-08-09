"""
Unit tests configuration module for vcs.
"""
import os

__all__ = (
    'TEST_HG_REPO', 'TEST_GIT_REPO', 'HG_REMOTE_REPO', 'GIT_REMOTE_REPO',
    'SCM_TESTS',
)

SCM_TESTS = ['hg', 'git']

TEST_GIT_REPO = os.environ.get('VCS_TEST_GIT_REPO', '/tmp/vcs-git')
GIT_REMOTE_REPO = 'git@github.com:lukaszb/vcs.git'

TEST_HG_REPO = os.environ.get('VCS_TEST_HG_REPO', '/tmp/vcs')
HG_REMOTE_REPO = 'http://bitbucket.org/marcinkuzminski/vcs'
TEST_HG_REPO_CLONE = os.environ.get('VCS_TEST_HG_REPO_CLONE', '/tmp/vcshgclone')
TEST_HG_REPO_PULL = os.environ.get('VCS_TEST_HG_REPO_PULL', '/tmp/vcshgpull')


PACKAGE_DIR = os.path.abspath(os.path.join(
    os.path.basename(__file__), '..'))


"""
Unit tests configuration module for vcs.
"""
import os

__all__ = (
    'TEST_HG_REPO', 'TEST_GIT_REPO', 'HG_REMOTE_REPO', 'GIT_REMOTE_REPO',
    'SCM_TESTS',
)

SCM_TESTS = ['hg']

TEST_HG_REPO = os.environ.get('VCS_TEST_HG_REPO', '/tmp/vcs')
TEST_GIT_REPO = os.environ.get('VCS_TEST_GIT_REPO', '/tmp/vcs-git')

HG_REMOTE_REPO = 'http://bitbucket.org/marcinkuzminski/vcs'
GIT_REMOTE_REPO = 'git@github.com:lukaszb/vcs.git'


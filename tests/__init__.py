"""
Unit tests for vcs_ library.

In order to run tests we need to prepare our environment first. Tests would be
run for each engine listed at ``conf.SCM_TESTS`` - keys are aliases from
``vcs.backends.BACKENDS``.

For each SCM we run tests for, we need some repository. We would use
repositories location from system environment variables or test suite defaults
- see ``conf`` module for more detail. We simply try to check if repository at
certain location exists, if not we would try to fetch them. At ``test_vcs`` or
``test_common`` we run unit tests common for each repository type and for
example specific mercurial tests are located at ``test_hg`` module.

Oh, and tests are run with nose_ test runner.

.. _vcs: http://bitbucket.org/marcinkuzminski/vcs
.. _nose: http://code.google.com/p/python-nose/

"""
from conf import *
from utils import VCSTestError, SCMFetcher

def setup_package():
    """
    Prepares whole package for tests which mainly means it would try to fetch
    test repositories or use already existing ones.
    """
    fetchers = {
        'hg': {
            'alias': 'hg',
            'test_repo_path': TEST_HG_REPO,
            'remote_repo': HG_REMOTE_REPO,
            'clone_cmd': 'hg clone',
        },
    }
    try:
        for scm, fetcher_info in fetchers.items():
            fetcher = SCMFetcher(**fetcher_info)
            fetcher.setup()
    except VCSTestError, err:
        raise RuntimeError(str(err))


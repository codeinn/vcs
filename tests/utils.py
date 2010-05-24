"""
Utilities for tests only. These are not or should not be used normally -
functions here are crafted as we don't want to use ``vcs`` to verify tests.
"""
import os
import os.path
import sys

from subprocess import Popen

class VCSTestError(Exception):
    pass

ALIASES = ['hg', 'git', 'svn', 'bzr']

def noob_guess_repo(path):
    """
    Returns one of: ``hg``, ``git``, ``svn``, ``bzr`` (in that order of
    precedence) for a given path.
    """
    if not os.path.isdir(path):
        raise VCSTestError("Given path %s is not a directory" % path)
    for key in ALIASES:
        dir = os.path.join(path, '.' + key)
        if os.path.isdir(dir):
            return key
    return None

def run_command(cmd, args):
    """
    Runs command on the system with given ``args``.
    """
    command = ' '.join((cmd, args))
    p = Popen(command, shell=True)
    status = os.waitpid(p.pid, 0)[1]
    return status

def eprint(msg):
    """
    Prints given ``msg`` into sys.stderr as nose test runner hides all output
    from sys.stdout by default and if we want to pipe stream somewhere we don't
    need those verbose messages anyway.
    Appends line break.
    """
    sys.stderr.write(msg)
    sys.stderr.write('\n')

class SCMFetcher(object):

    def __init__(self, alias, test_repo_path, remote_repo, clone_cmd):
        """
        :param clone_cmd: command which would clone remote repository; pass
          only first bits - remote path and destination would be appended
          using ``remote_repo`` and ``test_repo_path``
        """
        self.alias = alias
        self.test_repo_path = test_repo_path
        self.remote_repo = remote_repo
        self.clone_cmd = clone_cmd

    def setup(self):
        if not os.path.isdir(self.test_repo_path):
            self.fetch_repo()
        elif not noob_guess_repo(self.test_repo_path) == self.alias:
            raise RuntimeError("Repository at %s seems not to be %s powered"
                % (self.test_repo_path, self.alias))

    def fetch_repo(self):
        """
        Tries to fetch repository from remote path.
        """
        eprint("Seems that %s is empty. We need to fetch repository to run "
               "tests. Type repository path which would be cloned into %s\n"
               "(Hit enter to use: %s)" % (self.test_repo_path,
                self.test_repo_path, self.remote_repo))
        remote = raw_input() or self.remote_repo
        run_command(self.clone_cmd,  '%s %s' % (remote, self.test_repo_path))


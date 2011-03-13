"""
Utitlites aimed to help achieve mostly basic tasks.
"""
import os.path

from subprocess import Popen, PIPE
from vcs.exceptions import VCSError
from vcs.exceptions import RepositoryError
from vcs.utils.paths import abspath

ALIASES = ['hg', 'git']


def get_scm(path, search_recursively=False, explicit_alias=None):
    """
    Returns one of alias from ``ALIASES`` (in order of precedence same as
    shortcuts given in ``ALIASES``) and top working dir path for the given
    argument. If no scm-specific directory is found or more than one scm is
    found at that directory, ``VCSError`` is raised.

    :param search_recursively: if set to ``True``, this function would try to
      move up to parent directory every time no scm is recognized for the
      currently checked path. Default: ``False``.
    :param explicit_alias: can be one of available backend aliases, when given
      it will return given explicit alias in repositories under more than one
      version control, if explicit_alias is different than found it will raise
      VCSError
    """
    if not os.path.isdir(path):
        raise VCSError("Given path %s is not a directory" % path)

    def get_scms(path):
        return [(scm, path) for scm in get_scms_for_path(path)]

    found_scms = get_scms(path)
    while  not found_scms and search_recursively:
        newpath = abspath(path, '..')
        if newpath == path:
            break
        path = newpath
        found_scms = get_scms(path)

    if len(found_scms) > 1:
        for scm in found_scms:
            if scm[0] == explicit_alias:
                return scm
        raise VCSError('More than one [%s] scm found at given path %s'
                       % (','.join((x[0] for x in found_scms)), path))

    if len(found_scms) is 0:
        raise VCSError('No scm found at given path %s' % path)

    return found_scms[0]


def get_scms_for_path(path):
    """
    Returns all scm's found at the given path. If no scm is recognized
    - empty list is returned.

    :param path: path to directory which should be checked. May be callable.

    :raises VCSError: if given ``path`` is not a directory
    """
    from vcs.backends import get_backend
    if hasattr(path, '__call__'):
        path = path()
    if not os.path.isdir(path):
        raise VCSError("Given path %r is not a directory" % path)

    result = []
    for key in ALIASES:
        dirname = os.path.join(path, '.' + key)
        if os.path.isdir(dirname):
            result.append(key)
            continue
        # We still need to check if it's not bare repository as
        # bare repos don't have working directories
        try:
            get_backend(key)(path)
            result.append(key)
            continue
        except RepositoryError:
            # Wrong backend
            pass
        except VCSError:
            # No backend at all
            pass
    return result


def get_repo_paths(path):
    """
    Returns path's subdirectories which seems to be a repository.
    """
    repo_paths = []
    dirnames = (os.path.abspath(dirname) for dirname in os.listdir(path))
    for dirname in dirnames:
        try:
            get_scm(dirname)
            repo_paths.append(dirname)
        except VCSError:
            pass
    return repo_paths


def run_command(cmd, *args):
    """
    Runs command on the system with given ``args``.
    """
    command = ' '.join((cmd, args))
    p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = p.communicate()
    return p.retcode, stdout, stderr


def get_highlighted_code(name, code, type='terminal'):
    """
    If pygments are available on the system
    then returned output is colored. Otherwise
    unchanged content is returned.
    """
    import logging
    try:
        import pygments
        pygments
    except ImportError:
        return code
    from pygments import highlight
    from pygments.lexers import guess_lexer_for_filename, ClassNotFound
    from pygments.formatters import TerminalFormatter

    try:
        lexer = guess_lexer_for_filename(name, code)
        formatter = TerminalFormatter()
        content = highlight(code, lexer, formatter)
    except ClassNotFound:
        logging.debug("Couldn't guess Lexer, will not use pygments.")
        content = code
    return content

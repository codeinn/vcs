"""
Utitlites aimed to help achieve mostly basic tasks.
"""
import os.path

from subprocess import Popen, PIPE
from vcs.exceptions import VCSError

ALIASES = ['hg', 'git', 'svn', 'bzr']

def get_scm(path):
    """
    Returns one of alias from ``ALIASES`` (in order of precedence same as
    shortcuts given in ``ALIASES``) and top working dir path for the given
    argument. If no scm-specific directory is found or more than one scm is
    found at that directory, ``VCSError`` is raised.
    """
    if not os.path.isdir(path):
        raise VCSError("Given path %s is not a directory" % path)

    found_scms = []
    for key in ALIASES:
        dir = os.path.join(path, '.' + key)
        if os.path.isdir(dir):
            found_scms.append((key, path,))

    if len(found_scms) > 1:
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
    if hasattr(path, '__call__'):
        path = path()
    if not os.path.isdir(path):
        raise VCSError("Given path %r is not a directory" % path)

    result = []
    for key in ALIASES:
        dir = os.path.join(path, '.' + key)
        if os.path.isdir(dir):
            result.append(key)
    return result

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


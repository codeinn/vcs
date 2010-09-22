"""
Utitlites aimed to help achieve mostly basic tasks.
"""
import os
import os.path

from subprocess import Popen, PIPE
from vcs.exceptions import VCSError
from vcs.utils.paths import abspath

ALIASES = ['hg', 'git', 'svn', 'bzr']

def get_scm(path, search_recursively=False):
    """
    Returns one of alias from ``ALIASES`` (in order of precedence same as
    shortcuts given in ``ALIASES``) and top working dir path for the given
    argument. If no scm-specific directory is found, ``VCSError`` is raised
    unless ``search_recursively`` is set to ``True`` - in that case, function
    would try to find scm starting at given ``path`` and moving up. If we can't
    go up any further, ``VCSError`` is raised.
    """
    path = abspath(path)
    while True:
        if not os.path.isdir(path):
            raise VCSError("Given path %s is not a directory" % path)
        for key in ALIASES:
            dir = os.path.join(path, '.' + key)
            if os.path.isdir(dir):
                return key, path
        new_path = abspath(path, '..')
        if new_path == path:
            raise VCSError("%s is not a working dir for known scms" % path)
        else:
            path = new_path

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


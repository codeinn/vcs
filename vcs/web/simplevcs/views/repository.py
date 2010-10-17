import re

from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.template import RequestContext
from django.shortcuts import render_to_response

from vcs.exceptions import VCSError
from vcs.web.simplevcs.utils import get_repository


def browse_repository(request, template_name, repository=None,
        repository_path=None, repository_alias=None, revision=None,
        node_path='', extra_context={}):
    """
    Generic repository browser view.

    **Required arguments:**

    - Either ``repository`` or (``repository_path`` *and* ``repository_alias``
      is required

    - ``template_name``: The full name of a template to use in rendering the
      page.

    **Optional arguments:**

    - ``revision``: object with which backend may identify changeset. In
      example, mercurial backend recognizes *hex* or **short** strings, revision
      numbers (given as integer or string) or ``tip`` string. If none specified,
      most recent changeset (sometimes called ``tip``) is taken.

    - ``node_path``: relative location of the node in the repository (location
      to file or directory). By default this is an empty string which would
      retrieve root node from repository.

    - ``extra_context``: A dictionary of values to add to the template context.
      By default, this is an empty dictionary.

    **Template context:**

    In addition to ``extra_context``, the template's context will be:

    - ``repository``: same what was given or computed from ``repository_path``
      and ``repository_alias``

    - ``changeset``: based on the given ``revision`` or tip if none given

    - ``root``: repository's node on the given ``node_path``

    - ``readme_node``: ``FileNode`` instance if returning ``root`` is a
      ``DirNode`` and a readme file can be found at it's file listing (can be a
      file which name starts with *README*, with or without any extension,
      case is irrelevant); if no readme file could be found, None is returned

    """
    context = {}
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value

    try:
        repository = get_repository(repository, repository_path,
            repository_alias)
        changeset = repository.get_changeset(revision)
        root = changeset.get_node(node_path)
        if root.is_dir():
            readme_node = get_readme(root)
        else:
            readme_node = None
        context.update(dict(
            repository = repository,
            changeset = repository.get_changeset(),
            root = root,
            readme_node = readme_node,
        ))
    except VCSError, err:
        if settings.DEBUG:
            msg = 'DEBUG message: %s' % err
            messages.error(request, msg)
        else:
            raise Http404

    return render_to_response(template_name, context, RequestContext(request))


def get_readme(dirnode):
    """
    Returns readme ``FileNode`` or None if no readme file is found.
    """
    README_RE = re.compile(r'^README', re.IGNORECASE)
    for node in dirnode.files:
        if README_RE.match(node.name):
            return node
    return None


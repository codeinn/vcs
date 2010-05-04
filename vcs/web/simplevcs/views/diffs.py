from difflib import unified_diff
from django.contrib import messages
from django.template import RequestContext
from django.shortcuts import render_to_response

from vcs.exceptions import VCSError
from vcs.utils.diffs import get_udiff
from vcs.web.simplevcs.utils import get_repository

def diff_file(request, file_path, template_name, repository=None,
        repository_path=None, repository_alias=None, revision1=None,
        revision2=None, extra_context={}):
    """
    Generic repository browser view.

    **Required arguments:**

    - Either ``repository`` or (``repository_path`` *and* ``repository_alias``
      is required

    - ``file_path``: relative location of the file node in the repository.

    - ``revision1``: object identifying changeset on a backend.

    - ``revision2``: object identifying changeset on a backend.

    - ``template_name``: The full name of a template to use in rendering the
      page.

    **Optional arguments:**

    - ``extra_context``: A dictionary of values to add to the template context.
      By default, this is an empty dictionary.

    **Template context:**

    In addition to ``extra_context``, the template's context will be:

    - ``repository``: same what was given or computed from ``repository_path``
      and ``repository_alias``

    - ``file1``: ``FileNode`` retrieved by backend for given ``revision1`` param

    - ``file2``: ``FileNode`` retrieved by backend for given ``revision2`` param

    - ``diff_content``: unified diff for retrieved ``file1`` and ``file2``
      contents

    """
    context = {}
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value

    try:
        repository = get_repository(repository, repository_path,
            repository_alias)
        file1 = repository.request(file_path, revision1)
        file2 = repository.request(file_path, revision2)
        diff_content = get_udiff(file1.content, file2.content)

        context.update(dict(
            repository = repository,
            file1 = file1,
            file2 = file2,
            diff_content = diff_content,
        ))
    except VCSError, err:
        messages.error(request, str(err))

    return render_to_response(template_name, context, RequestContext(request))


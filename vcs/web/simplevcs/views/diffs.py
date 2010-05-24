from django.contrib import messages
from django.template import RequestContext
from django.shortcuts import render_to_response

from vcs.exceptions import VCSError
from vcs.utils.diffs import get_udiff, DiffProcessor
from vcs.web.simplevcs.utils import get_repository

def diff_file(request, file_path, template_name, repository=None,
        repository_path=None, repository_alias=None, revision_old=None,
        revision_new=None, extra_context={}):
    """
    Generic repository browser view.

    **Required arguments:**

    - Either ``repository`` or (``repository_path`` *and* ``repository_alias``
      is required

    - ``file_path``: relative location of the file node in the repository.

    - ``revision_old``: object identifying changeset at backend.

    - ``revision_new``: object identifying changeset at backend.

    - ``template_name``: The full name of a template to use in rendering the
      page.

    **Optional arguments:**

    - ``extra_context``: A dictionary of values to add to the template context.
      By default, this is an empty dictionary.

    **Template context:**

    In addition to ``extra_context``, the template's context will be:

    - ``repository``: same what was given or computed from ``repository_path``
      and ``repository_alias``

    - ``file_old``: ``FileNode`` retrieved by backend for given ``revision_old``
      param

    - ``file_new``: ``FileNode`` retrieved by backend for given ``revision_new``
      param

    - ``diff_content``: unified diff for retrieved ``file_old`` and ``file_new``
      contents

    """
    context = {}
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value

    try:
        repository = get_repository(repository, repository_path,
            repository_alias)
        file_old = repository.request(file_path, revision_old)
        file_new = repository.request(file_path, revision_new)
        diff_content = get_udiff(file_old, file_new)

        context.update(dict(
            repository = repository,
            file_old = file_old,
            file_new = file_new,
            diff_content = diff_content,
            differ = DiffProcessor(diff_content),
        ))
    except VCSError, err:
        messages.error(request, str(err))

    return render_to_response(template_name, context, RequestContext(request))


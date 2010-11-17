from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.template import RequestContext
from django.shortcuts import render_to_response

from vcs.exceptions import VCSError
from vcs.nodes import FileNode
from vcs.utils.diffs import get_udiff, DiffProcessor
from vcs.web.simplevcs.utils import get_repository

def diff_file(request, file_path, template_name, repository=None,
        repository_path=None, repository_alias=None, revision_old=None,
        revision_new=None, extra_context=None):
    """
    Generic repository browser view showing diff of specified file.

    **Required arguments:**

    - Either ``repository`` or (``repository_path`` *and* ``repository_alias``
      is required)

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
    if not extra_context:
        extra_context = {}
    context = {}
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value

    try:
        file_path.strip('/')
        if not file_path:
            raise VCSError("Cannot retrieve file diff for given path: %s"
                % file_path)
        repository = get_repository(repository, repository_path,
            repository_alias)
        changeset_old = repository.get_changeset(revision_old)
        changeset_new = repository.get_changeset(revision_new)
        file_old = changeset_old.get_node(file_path)
        file_new = changeset_new.get_node(file_path)
        diff_content = get_udiff(file_old, file_new)

        context.update(dict(
            repository = repository,
            file_old = file_old,
            file_new = file_new,
            diff_content = diff_content,
            differ = DiffProcessor(diff_content),
        ))
    except VCSError, err:
        if settings.DEBUG:
            msg = 'DEBUG message: %s' % err
            messages.error(request, msg)
        else:
            raise Http404

    return render_to_response(template_name, context, RequestContext(request))


def diff_changeset(request, template_name, repository=None,
        repository_path=None, repository_alias=None, revision=None,
        extra_context=None):
    """
    Generic repository browser view showing diffs for given revision.

    **Required arguments:**

    - Either ``repository`` or (``repository_path`` *and* ``repository_alias``
      is required

    - ``revision``: object identifying changeset at backend.

    - ``template_name``: The full name of a template to use in rendering the
      page.

    **Optional arguments:**

    - ``extra_context``: A dictionary of values to add to the template context.
      By default, this is an empty dictionary.

    **Template context:**

    In addition to ``extra_context``, the template's context will be:

    - ``repository``: same what was given or computed from ``repository_path``
      and ``repository_alias``

    - ``changeset``: ``Changeset`` retrieved by backend for given ``revision``
      param; nodes from ``added`` and ``changed`` attributes of the
      changeset have one extra attribute: ``diff`` which is instance of
      ``vcs.utils.diffs.DiffProcessor``

    """
    EXTRA_ATTR = 'diff'

    if not extra_context:
        extra_context = {}
    context = {}
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value

    try:
        repository = get_repository(repository, repository_path,
            repository_alias)
        changeset = repository.get_changeset(revision)

        # Added nodes
        empty = FileNode('EMPTY', content='')
        for node in changeset.added:
            if node.is_binary:
                # Should be handled at templates anyway
                continue
            udiff = get_udiff(empty, node)
            differ = DiffProcessor(udiff)
            setattr(node, EXTRA_ATTR, differ)

        # Changed nodes
        if changeset.parents:
            parent = changeset.parents[0]
            for node in changeset.changed:
                if node.is_binary:
                    # Should be handled at templates anyway
                    continue
                node_old = parent.get_node(node.path)
                udiff = get_udiff(node_old, node)
                differ = DiffProcessor(udiff)
                setattr(node, EXTRA_ATTR, differ)

        context.update(dict(
            repository = repository,
            changeset = changeset,
        ))
    except VCSError, err:
        if settings.DEBUG:
            msg = 'DEBUG message: %s' % err
            messages.error(request, msg)
        else:
            raise Http404

    return render_to_response(template_name, context, RequestContext(request))


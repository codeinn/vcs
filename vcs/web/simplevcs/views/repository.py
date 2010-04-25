from django.contrib import messages
from django.template import RequestContext
from django.shortcuts import render_to_response

from vcs.exceptions import VCSError

def browse_repository(request, repository, template_name, revision=None,
        node_path='', extra_context={}):
    """
    Generic repository browser.
    Provided context variables:

    - ``repository``: same what was given
    - ``changeset``: based on the given ``revision`` or tip if none given
    - ``root``: repositorie's node on the given ``node_path``

    """
    context = {}
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value

    try:
        context.update(dict(
            changeset = repository.get_changeset(),
            root = repository.request(node_path, revision=revision),
        ))
    except VCSError, err:
        messages.error(request, str(err))

    return render_to_response(template_name, context, RequestContext(request))


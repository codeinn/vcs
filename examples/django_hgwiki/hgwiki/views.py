import logging

from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_list, object_detail
from django.shortcuts import get_object_or_404

from hgwiki.models import Wiki
from vcs.web.simplevcs.utils import is_mercurial
from vcs.web.simplevcs.views import hgserve

def home(request, template_name='hgwiki/home.html'):
    """
    Returns hgwiki home page.
    """
    return direct_to_template(request, template=template_name)

def wiki_list(request, template_name='hgwiki/wiki_list.html'):
    """
    Returns wiki list page.
    """
    wiki_list_info = {
        'queryset': Wiki.objects.all(),
        'template_name': template_name,
        'template_object_name': 'wiki',
    }
    return object_list(request, **wiki_list_info)

def wiki_detail(request, slug, template_name='hgwiki/wiki_detail.html'):
    """
    Returns wiki detail page.
    """
    if is_mercurial(request):
        wiki = get_object_or_404(Wiki, slug=slug)
        return hgserve(request, wiki.repository, login_required=False)
    wiki_info = {
        'queryset': Wiki.objects.all(),
        'slug': slug,
        'template_name': template_name,
        'template_object_name': 'wiki',
    }
    return object_detail(request, **wiki_info)
wiki_detail.csrf_exempt = True # Needed for hgserve to work properly


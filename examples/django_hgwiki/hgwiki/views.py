import logging
import cStringIO
import traceback

from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_list, object_detail
from django.http import HttpResponse

from hgwiki.models import Wiki
from vcs.web.simplevcs.utils import basic_auth, get_mercurial_response,\
    is_mercurial

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
        return _wiki_hg(request, Wiki.objects.get(slug=slug))
    wiki_info = {
        'queryset': Wiki.objects.all(),
        'slug': slug,
        'template_name': template_name,
        'template_object_name': 'wiki',
    }
    return object_detail(request, **wiki_info)
wiki_detail.csrf_exempt = True

def _wiki_hg(request, wiki):
    user = request.user
    logging.debug("Calling basic_auth")
    user = basic_auth(request)
    request.user = user

    if user:
        pass
    else:
        response = HttpResponse()
        response.status_code = 401
        response['www-authenticate'] = 'Basic realm="%s"' % "MY REALM"
        return response

    try:
        response = get_mercurial_response(request,
            repo_path = wiki.repository.path,
            name = wiki.slug,
            baseurl = wiki.get_absolute_url(),
            allow_push = user.username,
            push_ssl = 'false',
        )
    except Exception, err:
        f = cStringIO.StringIO()
        traceback.print_exc(file=f)
        msg = "Got exception: %s\n\n%s"\
            % (err, f.getvalue())
        logging.error(msg)
        raise err
    logging.info("Returning response\n%s" % response)
    print "returning resposnse: \n%s" % response.__dict__
    return response

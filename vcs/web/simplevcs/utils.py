import os
import cgi
import copy
import pprint
import logging
import traceback
import cStringIO
import pagination.middleware

from mercurial.hgweb.request import wsgirequest, normalize
from mercurial.hgweb import hgweb

from django.http import HttpResponse
from django.conf import settings
from django.core.exceptions import PermissionDenied, ImproperlyConfigured
from django.shortcuts import redirect, render_to_response, get_object_or_404
from django.utils.translation import ugettext as _
from django.utils.encoding import smart_str
from django.views.generic.simple import direct_to_template

from django.contrib.auth.models import User, AnonymousUser
from django.contrib.auth import authenticate

from projector.models import Project
from projector.permissions import ProjectPermission
from projector.settings import *

class MercurialRequest(wsgirequest):
    """
    We need to override ``__init__``, ``respond`` and ``write``
    methods in order to properly fake mercurial client request.
    Those methods need to operate on Django's standard
    ``HttpResponse``.
    """
    _already_responded = False
    _response_written = False

    def __init__(self, request):
        """
        Initializes ``MercurialRequest`` and make necessary
        changes to the ``env`` attribute (which is ``META``
        attribute of the given request).
        """

        # Before we set environment for mercurial
        # we need to fix (if needed) it's PATH_INFO
        if not request.META['PATH_INFO'].endswith == '/':
            request.META['PATH_INFO'] += '/'
        self.env = request.META
        logging.critical("Settings REMOTE_USER to '%s'" % request.user.username)
        self.env['SCRIPT_NAME'] = request.path
        self.env['PATH_INFO'] ='/'
        self.env['REMOTE_USER'] = request.user.username

        self.err = self.env['wsgi.errors']
        self.inp = self.env['wsgi.input']
        self.headers = []

        self.form = normalize(cgi.parse(self.inp, self.env, keep_blank_values=1))
        self._response = HttpResponse()

    def write(self, thing):
        """
        Writes to the constructed response object.
        """
        if hasattr(thing, "__iter__"):
            for part in thing:
                self.write(part)
        else:
            thing = str(thing)
            self._response.write(thing)

    def respond(self, status, type=None, filename=None, length=0):
        """
        Starts responding (once): sets status code and headers.
        """
        if not self._already_responded:
            logging.debug("respond status: %s" % status)
            logging.debug("respond type: %s" % type)
            logging.debug("respond filename: %s" % filename)
            logging.debug("respond length: %s" % length)

            self._response.status_code = status
            self._response['content-type'] = type

            for key, value in self.headers:
                self._response[key] = value

            self._already_responded = True
            #self._headers = []

    def get_response(self, hgweb):
        """
        Returns ``HttpResponse`` object created by this
        request, using given ``hgweb``.
        """
        if not self._response_written:
            self._response.write(''.join(
                (each for each in hgweb.run_wsgi(self))))
            self._response_written = True
        return self._response

class MercurialServer(object):
    """
    Mimics functionality of ``hgweb``.
    """
    def __init__(self, repo_path, **webinfo):
        self._hgserve = hgweb(repo_path)
        self.setup_web(**webinfo)

    def ui_config(self, section, key, value):
        self._hgserve.repo.ui.setconfig(
            section, key, smart_str(value))

    def setup_web(self, **webinfo):
        for key, value in webinfo.items():
            if value is not None:
                self.ui_config('web', key, value)
                #self._hgserve.repo.ui.setconfig('web', key, smart_str(value))

    def get_response(self, request):
        mercurial_request = MercurialRequest(request)
        response = mercurial_request.get_response(self._hgserve)
        return response

def get_mercurial_response(request, repo_path, name, baseurl, push_ssl='false',
    description='', contact='', allow_push=None, username=None):
    """
    Returns ``HttpResponse`` object prepared basing
    on the given ``hgserve`` instance.
    """
    repo_path = str(repo_path) # mercurial requires str, not unicode
    webinfo = dict(
        name = name,
        baseurl = baseurl,
        push_ssl = push_ssl,
        description = description,
        contact = contact,
        allow_push = allow_push,
    )
    mercurial_server = MercurialServer(repo_path, **webinfo)
    if username is not None:
        mercurial_server.ui_config('ui', 'username', smart_str(username))
    response = mercurial_server.get_response(request)
    #logging.info("Mercurial server configured:\n%s"
    #    % pprint.pformat(list(mercurial_server._hgserve.repo.ui.walkconfig())))
    return response

class NotMercurialRequestError(Exception):
    pass

def hgrepo_detail(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)
    realm = HG_BASIC_AUTH_REALM

    logging.debug("Check if requst is mercurial")
    if not is_mercurial(request):
        logging.warn("simplehg.hgrepo_detail request not from mercurial client!?")
        raise NotMercurialRequestError("Only mercurial requests are allowed here")

    if project.is_public() and request.method == 'GET':
        logging.debug("Setting AnonymousUser user.")
        user = AnonymousUser()
    else:
        logging.debug("Calling basic_auth")
        user = basic_auth(request)
        request.user = user

    # Check permissions
    if user:
        check = ProjectPermission(user)
        # Reading from repository (clone/pull/etc)
        if project.is_private() and request.method == 'GET' and \
            not check.read_repository_project(project):
            logging.warn("User %s does not have permission to read this repository (%s)."
                % (user, project))
            raise PermissionDenied()
        # Writing to repository (push)
        if request.method == 'POST' and \
            not check.write_repository_project(project):
            logging.warn("User %s does not have permission to write to this repository."
                % user)
            raise PermissionDenied()
    else:
        response = HttpResponse()
        response.status_code = 401
        response['www-authenticate'] = 'Basic realm="%s"' % realm
        return response

    try:
        response = get_mercurial_response(request,
            repo_path = project._get_repo_path(),
            name = project.name,
            contact = project.author.email,
            description = project.description,
            baseurl = project.get_absolute_url(),
            allow_push = user.username,
            push_ssl = HG_PUSH_SSL,
            username = user.username,
            )
    except Exception, err:
        f = cStringIO.StringIO()
        traceback.print_exc(file=f)
        msg = "Got exception: %s\n\n%s"\
            % (err, f.getvalue())
        logging.error(msg)
        raise err
    print "returning resposnse: \n%s" % response.__dict__
    return response

def is_mercurial(request):
    """
    Returns True if request's target is mercurial server -
    header ``HTTP_ACCEPT`` of such request would start with
    ``application/mercurial``.
    """
    http_accept = request.META.get('HTTP_ACCEPT')
    if http_accept and http_accept.startswith('application/mercurial'):
        return True
    return False

def basic_auth(request):
    """
    Returns ``django.contrib.auth.models.User`` object
    if authorization was successful and ``None`` otherwise.
    """
    http_authorization = request.META.get('HTTP_AUTHORIZATION')
    user = None
    if http_authorization and http_authorization.startswith('Basic '):
        base64_hash = http_authorization.lstrip('Basic ')
        credentials = base64_hash.decode('base64')
        username, password = credentials.split(':', 1)
        user = authenticate(username=username, password=password)
    return user

class PaginationMiddleware(pagination.middleware.PaginationMiddleware):
    """
    Inserts a variable representing the current page onto the request object if
    it exists in either **GET** or **POST** portions of the request.
    This, slightly modified version of original
    ``pagination.middleware.PaginationMiddleware`` won't break ``mercurial``
    requests.
    """
    def process_request(self, request):
        if is_mercurial(request):
            # Won't continue on mercurial request as
            # it would break the response
            return
        super(PaginationMiddleware, self).process_request(request)


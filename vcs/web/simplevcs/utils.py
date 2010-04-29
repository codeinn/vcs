import cgi
import logging
import traceback
import cStringIO

from mercurial.hgweb.request import wsgirequest, normalize
from mercurial.hgweb import hgweb

from django.http import HttpResponse
from django.utils.encoding import smart_str
from django.contrib.auth import authenticate

from vcs.web.simplevcs.settings import BASIC_AUTH_REALM

class MercurialRequest(wsgirequest):
    """
    We need to override ``__init__``, ``respond`` and ``write`` methods in
    order to properly fake mercurial client request.  Those methods need to
    operate on Django's standard ``HttpResponse``.
    """
    _already_responded = False
    _response_written = False

    def __init__(self, request):
        """
        Initializes ``MercurialRequest`` and make necessary changes to the
        ``env`` attribute (which is ``META`` attribute of the given request).
        """

        # Before we set environment for mercurial
        # we need to fix (if needed) it's PATH_INFO
        if not request.META['PATH_INFO'].endswith == '/':
            request.META['PATH_INFO'] += '/'
        self.env = request.META
        self.env['SCRIPT_NAME'] = request.path
        self.env['PATH_INFO'] ='/'
        if request.user:
            self.env['REMOTE_USER'] = request.user.username

        self.err = self.env['wsgi.errors']
        self.inp = self.env['wsgi.input']
        self.headers = []

        self.form = normalize(cgi.parse(self.inp, self.env,
            keep_blank_values=1))
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
            self._response.status_code = status
            self._response['content-type'] = type

            for key, value in self.headers:
                self._response[key] = value

            self._already_responded = True

    def get_response(self, hgweb):
        """
        Returns ``HttpResponse`` object created by this request, using given
        ``hgweb``.
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

    def get_response(self, request):
        mercurial_request = MercurialRequest(request)
        response = mercurial_request.get_response(self._hgserve)
        return response

def get_mercurial_response(request, repo_path, baseurl=None, name=None,
    push_ssl='false', description=None, contact=None, allow_push=None,
    username=None):
    """
    Returns ``HttpResponse`` object prepared basing on the given ``hgserve``
    instance.
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
    return response

def is_mercurial(request):
    """
    Returns True if request's target is mercurial server - header
    ``HTTP_ACCEPT`` of such request would start with ``application/mercurial``.
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
        base64_hash = http_authorization[len('Basic '):]
        credentials = base64_hash.decode('base64')
        username, password = credentials.split(':', 1)
        user = authenticate(username=username, password=password)
    return user

def ask_basic_auth(request, realm=BASIC_AUTH_REALM):
    """
    Returns HttpResponse with status code 401 (HTTP_AUTHORIZATION) to ask user
    to authorize.
    """
    response = HttpResponse()
    response.status_code = 401
    response['www-authenticate'] = 'Basic realm="%s"' % realm
    return response

def log_error(error):
    """
    Logs traceback and error itself.
    """
    assert(isinstance(error, Exception))
    f = cStringIO.StringIO()
    traceback.print_exc(file=f)
    msg = "Got exception: %s\n\n%s"\
        % (error, f.getvalue())
    logging.error(msg)


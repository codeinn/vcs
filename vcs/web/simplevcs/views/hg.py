"""
Semi generic views which helps to reponse for requests comming from
specific SCM clients.
"""
import logging
import cStringIO
import traceback

from vcs.web.simplevcs.settings import PUSH_SSL, ALWAYS_REQUIRE_LOGIN
from vcs.web.simplevcs.utils import ask_basic_auth, basic_auth,\
    get_mercurial_response, is_mercurial
from vcs.web.exceptions import RequestError
from vcs.web.simplevcs.exceptions import NotMercurialRequest

def hgserve(request, repo_path, login_required=True, auth_callback=None):
    """
    Returns mimic of mercurial response. Would raise ``NotMercurialRequest`` if
    request is not recognized as one comming from mercurial agent.

    :param repo_path: path to local mercurial repository on which request would
      be made

    :param login_required=True: if set to False, would not require user
      to authenticate at all (with one exception, see note below)

    .. note::
       by default ``VCS_ALWAYS_REQUIRE_LOGIN`` is set to True and if not
       changed, would cause this function to require authentication from all
       requests (and ``login_required`` would *NOT* be checked). If, on the
       other hand, settings are configured that ``VCS_ALWAYS_REQUIRE_LOGIN`` is
       False, then authorization would be required only if login_required is
       True.

    :param auth_callback=None: callable function, may be passed only if
      login_required was True; would be called *after* authorization, with
      ``user`` as parameter; may be used i.e. for permission checks

    """

    if not is_mercurial(request):
        msg = "hgserve used but request doesn't come from mercurial client"
        raise NotMercurialRequest(msg)
    if not login_required and auth_callback:
        raise RequestError("auth_callback passed but login is not required - "
            "cannot run callback without authorized user")
    if auth_callback and not callable(auth_callback):
        raise RequestError("auth_callback passed but is not callable")
    # Need to catch all exceptions in order to show them if something
    # goes wrong within mercurial request to response phases
    try:
        if request.user and not request.user.is_active:
            user = basic_auth(request)
        request.user = user

        # check if should ask for credentials
        '''
        if (ALWAYS_REQUIRE_LOGIN and not user.is_active) or (not user and
            (login_required or request.method == 'POST')):
            return ask_basic_auth(request)
        #'''
        '''
        if login_required and not user:
            return ask_basic_auth(request)
        if not user and request.method == 'POST':
            return ask_basic_auth(request)
        '''
        if not user and (login_required or request.method == 'POST'):
            return ask_basic_auth
        #'''
        # run auth_callback if given
        auth_callback and auth_callback(user)
        mercurial_info = {
            'repo_path': repo_path,
            'push_ssl': PUSH_SSL,
        }

        if user and user.is_active:
            mercurial_info['allow_push'] = user.username

        response = get_mercurial_response(request, **mercurial_info)
    except (KeyboardInterrupt, MemoryError):
        raise
    except Exception, err:
        print err
        f = cStringIO.StringIO()
        traceback.print_exc(file=f)
        msg = "Got exception: %s\n\n%s"\
            % (err, f.getvalue())
        logging.error(msg)
        raise err
    return response


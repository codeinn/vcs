import sys
import logging
import cStringIO
import traceback

from vcs.web.simplevcs.settings import PUSH_SSL
from vcs.web.simplevcs.utils import ask_basic_auth, basic_auth,\
    get_mercurial_response, is_mercurial

def hgserve(request, repository, login_required=True):
    """
    Returns mimic of mercurial response.

    @param repository: should be instance of
       ``vcs.web.simplevcs.models.Repository``
    """
    if not is_mercurial(request):
        sys.stderr.write("hgserve used but request doesn't come "
            "from mercurial client")
        raise Exception
    if repository.type != 'hg':
        sys.stderr.write("hgserve used but repository.type != 'hg "
            "(it is '%s')" % repository.type)
        raise Exception
    try:
        user = basic_auth(request)
        request.user = user

        if login_required and not user:
            return ask_basic_auth(request)
        if not user and request.method == 'POST':
            return ask_basic_auth(request)

        mercurial_info = {
            'repo_path': repository.path,
            'push_ssl': PUSH_SSL,
        }

        if user and user.is_active:
            mercurial_info['allow_push'] = user.username

        response = get_mercurial_response(request, **mercurial_info)
    except Exception, err:
        print err
        f = cStringIO.StringIO()
        traceback.print_exc(file=f)
        msg = "Got exception: %s\n\n%s"\
            % (err, f.getvalue())
        print msg
        logging.error(msg)
        raise err
    return response


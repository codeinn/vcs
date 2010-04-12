from pprint import pformat
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from vcs import VCSError, BACKENDS

AVAILABLE_BACKENDS = getattr(settings, 'VCS_AVAILABLE_BACKENDS',
    BACKENDS.keys())
if not set(AVAILABLE_BACKENDS).issubset(set(BACKENDS.keys())):
    raise ImproperlyConfigured("Unsupported backends specified at "
        "VCS_AVAILABLE_BACKENDS setting.\nAvailable aliases:\n%s"
        % pformat(BACKENDS.keys()))




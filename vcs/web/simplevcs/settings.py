from pprint import pformat
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from vcs import BACKENDS

AVAILABLE_BACKENDS = getattr(settings, 'VCS_AVAILABLE_BACKENDS',
    BACKENDS.keys())
if not set(AVAILABLE_BACKENDS).issubset(set(BACKENDS.keys())):
    raise ImproperlyConfigured("Unsupported backends specified at "
        "VCS_AVAILABLE_BACKENDS setting.\nAvailable aliases:\n%s"
        % pformat(BACKENDS.keys()))

PUSH_SSL = getattr(settings, 'DEBUG', False) and 'false' or 'true'

BASIC_AUTH_REALM = getattr(settings, 'VCS_BASIC_AUTH_REALM', 'Basic Auth Realm')

ALWAYS_REQUIRE_LOGIN = getattr(settings, 'VCS_ALWAYS_REQUIRE_LOGIN', True)


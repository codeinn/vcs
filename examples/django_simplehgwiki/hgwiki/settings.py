import os
from django.conf import settings

REPOSITORIES_DIR = os.path.abspath(os.path.join(
    settings.PROJECT_ROOT, 'repos')
)

if not os.path.isdir(REPOSITORIES_DIR):
    os.mkdir(REPOSITORIES_DIR)



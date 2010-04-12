from django.db import models
from django.core.exceptions import ValidationError
from vcs import get_repo
from vcs.utils.lazy import LazyProperty
from vcs.web.simplevcs.settings import AVAILABLE_BACKENDS

def validate_type(type):
    if type not in AVAILABLE_BACKENDS:
        raise ValidationError("Cannot use type %r" % type)

class Repository(models.Model):
    type = models.CharField(max_length=32, validators=[validate_type])
    path = models.CharField(max_length=1024, unique=True)

    @LazyProperty
    def _repo(self):
        repo = get_repo(self.type, path=self.path)
        return repo

    @LazyProperty
    def revisions(self):
        return self._repo.revisions

    def __unicode__(self):
        return self.path

    def init(self):
        self._repo.init()

    def get_changeset(self, revision=None):
        return self._repo.get_changeset(revision)

    def save(self, *args, **kwargs):
        self._repo.init()
        super(Repository, self).save(*args, **kwargs)


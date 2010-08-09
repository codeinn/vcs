from django.db import models
from django.core.exceptions import ValidationError

from vcs import get_repo, get_backend, RepositoryError
from vcs.utils.lazy import LazyProperty
from vcs.web.simplevcs.settings import AVAILABLE_BACKENDS
from vcs.web.simplevcs.managers import RepositoryManager

def validate_alias(alias):
    if alias not in AVAILABLE_BACKENDS:
        raise ValidationError("Cannot use alias %r" % alias)

class Repository(models.Model):
    alias = models.CharField(max_length=32, validators=[validate_alias])
    path = models.CharField(max_length=255, unique=True)

    objects = RepositoryManager()

    @LazyProperty
    def _repo(self):
        repo = get_repo(self.alias, path=self.path)
        return repo

    @LazyProperty
    def revisions(self):
        return self._repo.revisions

    def __unicode__(self):
        return self.path

    def __len__(self):
        return len(self._repo)

    def __getslice__(self, i, j):
        repo = self._repo
        return repo.__getslice__(i, j)

    def __iter__(self):
        for changeset in self._repo:
            yield changeset

    def request(self, path, revision=None):
        return self._repo.request(path, revision)

    def get_changeset(self, revision=None):
        return self._repo.get_changeset(revision)

    def get_changesets(self, *args, **kwargs):
        return self._repo.get_changesets(*args, **kwargs)

    def save(self, clone_url=None, *args, **kwargs):
        if clone_url:
            backend = get_backend(self.alias)
            try:
                self.repo = backend(self.path, create=True, clone_url=clone_url)
            except RepositoryError:
                self.repo = backend(self.path, clone_url=clone_url)
        else:
            try:
                self.repo = get_repo(self.alias, path=self.path, create=True)
            except RepositoryError:
                self.repo = get_repo(self.alias, path=self.path)
        super(Repository, self).save(*args, **kwargs)


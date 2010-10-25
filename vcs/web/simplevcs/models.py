from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from vcs import get_repo, get_backend, RepositoryError
from vcs.utils.lazy import LazyProperty
from vcs.utils.paths import get_dir_size
from vcs.web.simplevcs.settings import AVAILABLE_BACKENDS
from vcs.web.simplevcs.managers import RepositoryManager

from warnings import warn

def validate_alias(alias):
    if alias not in AVAILABLE_BACKENDS:
        raise ValidationError("Cannot use alias %r" % alias)

class Repository(models.Model):
    alias = models.CharField(max_length=32, validators=[validate_alias])
    path = models.CharField(max_length=255, unique=True)

    objects = RepositoryManager()

    @LazyProperty
    def _repo(self):
        repo = get_repo(path=self.path, alias=self.alias)
        return repo

    @LazyProperty
    def revisions(self):
        return self._repo.revisions

    def __unicode__(self):
        return self.alias

    def __str__(self):
        return self.path

    def __bool__(self):
        return self._repo is not None

    def __len__(self):
        return len(self._repo)

    def __getslice__(self, i, j):
        repo = self._repo
        return repo.__getslice__(i, j)

    def __iter__(self):
        for changeset in self._repo:
            yield changeset

    def request(self, path, revision=None):
        warn("request method is deprecated - use get_changeset to fetch a "
             "changeset and then get_node explicity", DeprecationWarning)
        changeset = self._repo.get_changeset(revision)
        return changeset.get_node(path)

    def get_changeset(self, revision=None):
        return self._repo.get_changeset(revision)

    def get_changesets(self, *args, **kwargs):
        return self._repo.get_changesets(*args, **kwargs)

    def save(self, clone_url=None, *args, **kwargs):
        if clone_url:
            backend = get_backend(self.alias)
            try:
                self.repo = backend(self.path, create=True, src_url=clone_url)
            except RepositoryError:
                self.repo = backend(self.path, src_url=clone_url)
        else:
            try:
                self.repo = get_repo(path=self.path, alias=self.alias,
                    create=True)
            except RepositoryError:
                self.repo = get_repo(path=self.path, alias=self.alias)
        super(Repository, self).save(*args, **kwargs)


class RepositoryInfo(models.Model):
    repository = models.OneToOneField(Repository, verbose_name=_('repository'),
        related_name='info')
    clone_count = models.PositiveIntegerField(_('clone count'), default=0)
    push_count = models.PositiveIntegerField(_('push count'), default=0)
    size = models.PositiveIntegerField(_('size'), default=0)

    def __unicode__(self):
        return u'<RepositoryInfo id=%s for Repository %s | %s>' % (self.id,
            self.repository.id, self.repository.path)

    def get_repo_size(self):
        """
        Returns current size of repository directory.
        """
        size = get_dir_size(self.repository.path)
        if size != self.size:
            self.size = size
            if self.id:
                RepositoryInfo.objects.filter(id=self.id).update(size=size)
        return size

from vcs.web.simplevcs.listeners import start_listening
start_listening()


import os

from django.db import models
from django.template.defaultfilters import slugify

from vcs.web.simplevcs.models import Repository
from hgwiki.settings import REPOSITORIES_DIR

class Wiki(models.Model):
    name = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(unique=True)
    repository = models.ForeignKey(Repository)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        repo_path = os.path.abspath(os.path.join(
            REPOSITORIES_DIR, self.slug))
        print repo_path
        self.repository = Repository.objects.create(
                type='hg',
                path=repo_path,
        )
        super(Wiki, self).save(*args, **kwargs)


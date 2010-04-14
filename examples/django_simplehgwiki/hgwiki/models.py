import os

from django.db import models
from django.template.defaultfilters import slugify

from vcs.web.simplevcs.models import Repository
from hgwiki.settings import REPOSITORIES_DIR

class Wiki(models.Model):
    title = models.CharField(max_length=64, unique=True)
    slug = models.SlugField(unique=True)
    repository = models.ForeignKey(Repository)
    content = models.TextField(default='')

    class Meta:
        ordering = ('title',)

    def __unicode__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        repo_path = os.path.abspath(os.path.join(
            REPOSITORIES_DIR, self.slug))
        try:
            self.repository
        except Repository.DoesNotExist:
            self.repository = Repository.objects.create(
                    type='hg',
                    path=repo_path,
            )
        super(Wiki, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('hgwiki_wiki_detail', (), {
            'slug': self.slug})


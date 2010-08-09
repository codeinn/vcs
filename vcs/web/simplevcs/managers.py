from django.db import models

class RepositoryManager(models.Manager):

    def create(self, clone_url=None, *args, **kwargs):
        """
        Allows ``clone_url`` to be passed and if so, would try to clone
        repository from this location.
        """
        obj = self.model(**kwargs)
        self._for_write = True
        obj.save(force_insert=True, using=self.db, clone_url=clone_url)
        return obj


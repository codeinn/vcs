import logging

from django.db.models import F
from django.db.models.signals import post_save

from vcs.utils.paths import get_dir_size
from vcs.web.simplevcs.models import Repository, RepositoryInfo
from vcs.web.simplevcs.signals import post_clone, post_push

def repository_created_handler(sender, instance, **kwargs):
    if kwargs['created'] is not True:
        # Repository was *not* created at this time
        return
    info = RepositoryInfo.objects.create(
        repository=instance)
    return info

def post_clone_handler(sender, repo_path, ip, username, **kwargs):
    logging.debug("Post CLONE: %s | %s | %s" % (repo_path, ip, username))
    if repo_path:
        RepositoryInfo.objects.filter(repository__path=repo_path) \
            .update(clone_count=F('clone_count') + 1)

def post_push_handler(sender, repo_path, ip, username, **kwargs):
    logging.debug("Post PUSH: %s | %s | %s" % (repo_path, ip, username))
    if repo_path:
        # Update repository info instance
        size = get_dir_size(repo_path)
        updated = RepositoryInfo.objects\
            .filter(repository__path=repo_path)\
            .update(
                push_count=F('push_count') + 1,
                size=size,
            )
        if updated == 0:
            RepositoryInfo.objects.create(
                repository=Repository.objects.get(path=repo_path),
                push_count=1,
                size=size,
            )


def start_listening():
    """
    Should be called at the end of the ``models`` module.
    """
    post_clone.connect(post_clone_handler, sender=None)
    post_push.connect(post_push_handler, sender=None)

    post_save.connect(repository_created_handler, sender=Repository)


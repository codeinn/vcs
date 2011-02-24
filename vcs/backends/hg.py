#!/usr/bin/env python
# encoding: utf-8
#
# Copyright (c) 2010 Marcin Kuzminski,Lukasz Balcerzak.  All rights reserved.
#
"""
Created on Apr 8, 2010

:author: marcink,lukaszb
"""
import os
import re
import time
import urllib2
import posixpath
import errno

from mercurial import ui
from mercurial.context import short
from mercurial.error import RepoError, RepoLookupError, Abort
from mercurial.localrepo import localrepository
from mercurial.node import hex
from mercurial.commands import clone, pull
from mercurial.context import memctx, memfilectx

from vcs.backends.base import BaseRepository, BaseChangeset, \
    BaseInMemoryChangeset
from vcs.exceptions import RepositoryError
from vcs.exceptions import EmptyRepositoryError
from vcs.exceptions import ChangesetError
from vcs.exceptions import ChangesetDoesNotExistError
from vcs.exceptions import NodeDoesNotExistError
from vcs.nodes import FileNode, DirNode, NodeKind, RootNode, RemovedFileNode, \
    RemovedFileNodesGenerator, ChangedFileNodesGenerator, \
    AddedFileNodesGenerator
from vcs.utils.lazy import LazyProperty
from vcs.utils.ordered_dict import OrderedDict
from vcs.utils.paths import abspath, get_dirs_for_path
from vcs.utils import safe_unicode, makedate, date_fromtimestamp

class MercurialRepository(BaseRepository):
    """
    Mercurial repository backend
    """

    def __init__(self, repo_path, create=False, baseui=None, src_url=None,
                 update_after_clone=False):
        """
        Raises RepositoryError if repository could not be find at the given
        ``repo_path``.

        :param repo_path: local path of the repository
        :param create=False: if set to True, would try to craete repository if
           it does not exist rather than raising exception
        :param baseui=None: user data
        :param src_url=None: would try to clone repository from given location
        :param update_after_clone=False: sets update of working copy after
          making a clone
        """

        self.path = abspath(repo_path)
        self.baseui = baseui or ui.ui()
        # We've set path and ui, now we can set repo itself
        self._set_repo(create, src_url, update_after_clone)
        self.revisions = list(self.repo)
        self.changesets = {}

    @LazyProperty
    def name(self):
        return os.path.basename(self.path)

    @LazyProperty
    def branches(self):
        """Get's branches for this repository
        """

        if not self.revisions:
            return {}

        def _branchtags(localrepo):
            """
            Patched version of mercurial branchtags to not return the closed
            branches
            :param localrepo: locarepository instance
            """

            bt = {}
            for bn, heads in localrepo.branchmap().iteritems():
                tip = heads[-1]
                if 'close' not in localrepo.changelog.read(tip)[5]:
                    bt[bn] = tip
            return bt

        sortkey = lambda ctx: ctx[0] #sort by name
        _branches = [(n.decode('utf-8'), hex(h),) for n, h in _branchtags(self.repo).items()]

        return OrderedDict(sorted(_branches, key=sortkey, reverse=False))

    @LazyProperty
    def tags(self):
        """Get's tags for this repository
        """

        if not self.revisions:
            return {}

        sortkey = lambda ctx: ctx[0] #sort by name
        _tags = [(n.decode('utf-8'), hex(h),) for n, h in self.repo.tags().items()]

        return OrderedDict(sorted(_tags, key=sortkey, reverse=True))

    def _set_repo(self, create, src_url=None, update_after_clone=False):
        """
        Function will check for mercurial repository in given path and return
        a localrepo object. If there is no repository in that path it will raise
        an exception unless ``create`` parameter is set to True - in that case
        repository would be created and returned.
        If ``src_url`` is given, would try to clone repository from the
        location at given clone_point. Additionally it'll make update to
        working copy accordingly to ``update_after_clone`` flag
        """
        try:
            if src_url:
                url = self._get_url(src_url)
                opts = {}
                if not update_after_clone:
                    opts.update({'noupdate':True})
                try:
                    clone(self.baseui, url, self.path, **opts)
                except urllib2.URLError:
                    raise Abort("Got HTTP 404 error")
                # Don't try to create if we've already cloned repo
                create = False
            self.repo = localrepository(self.baseui, self.path, create=create)
        except (Abort, RepoError), err:
            if create:
                msg = "Cannot create repository at %s. Original error was %s"\
                    % (self.path, err)
            else:
                msg = "Not valid repository at %s. Original error was %s"\
                    % (self.path, err)
            raise RepositoryError(msg)

    @LazyProperty
    def in_memory_changeset(self):
        return MercurialInMemoryChangeset(self)

    @LazyProperty
    def description(self):
        undefined_description = 'unknown'
        return self.repo.ui.config('web', 'description',
                                   undefined_description, untrusted=True)
    @LazyProperty
    def contact(self):
        from mercurial.hgweb.common import get_contact
        undefined_contact = 'Unknown'
        return get_contact(self.repo.ui.config) or undefined_contact

    @LazyProperty
    def last_change(self):
        """
        Returns last change made on this repository as datetime object
        """
        return date_fromtimestamp(self._get_mtime(), makedate()[1])

    def _get_mtime(self):
        try:
            return time.mktime(self.get_changeset().date.timetuple())
        except RepositoryError:
            #fallback to filesystem
            cl_path = os.path.join(self.path, '.hg', "00changelog.i")
            st_path = os.path.join(self.path, '.hg', "store")
            if os.path.exists(cl_path):
                return os.stat(cl_path).st_mtime
            else:
                return os.stat(st_path).st_mtime

    def _get_hidden(self):
        return self.repo.ui.configbool("web", "hidden", untrusted=True)

    def _get_revision(self, revision):
        if len(self.revisions) == 0:
            raise EmptyRepositoryError("There are no changesets yet")
        if revision in (None, 'tip', -1):
            revision = self.revisions[-1]
        if isinstance(revision, int) and revision not in self.revisions:
            raise ChangesetDoesNotExistError("Revision %r does not exist "
                "for this repository %s" % (revision, self))
        elif isinstance(revision, (str, unicode)) and revision.isdigit() \
                                                    and len(revision) < 12:
            revision = int(revision)
        elif isinstance(revision, (str, unicode)):
            pattern = re.compile(r'^[[0-9a-fA-F]{12}|[0-9a-fA-F]{40}]$')
            if not pattern.match(revision):
                raise ChangesetDoesNotExistError("Revision %r does not exist "
                    "for this repository %s" % (revision, self))
        return revision

    def _get_archives(self, archive_name='tip'):
        allowed = self.baseui.configlist("web", "allow_archive", untrusted=True)
        for i in [('zip', '.zip'), ('gz', '.tar.gz'), ('bz2', '.tar.bz2')]:
            if i[0] in allowed or self.repo.ui.configbool("web", "allow" + i[0],
                                                untrusted=True):
                yield {"type" : i[0], "extension": i[1], "node": archive_name}

    def _get_url(self, url):
        """
        Returns normalized url. If schema is not given, would fall to filesystem
        (``file://``) schema.
        """
        url = str(url)
        if url != 'default' and not '://' in url:
            url = '://'.join(('file', url))
        return url

    def get_changeset(self, revision=None):
        """
        Returns ``MercurialChangeset`` object representing repository's
        changeset at the given ``revision``.
        """
        revision = self._get_revision(revision)
        if not self.changesets.has_key(revision):
            changeset = MercurialChangeset(repository=self, revision=revision)
            self.changesets[changeset.revision] = changeset
            self.changesets[changeset.raw_id] = changeset
            self.changesets[changeset.short_id] = changeset
        return self.changesets[revision]

    def get_changesets(self, limit=10, offset=None):
        """
        Return last n number of ``MercurialChangeset`` specified by limit
        attribute if None is given whole list of revisions is returned

        :param limit: int limit or None
        :param offset: int offset
        """
        count = self.count()
        offset = offset or 0
        limit = limit or None
        i = 0
        while True:
            if limit and i == limit:
                break
            i += 1
            rev = count - offset - i
            if rev < 0:
                break
            yield self.get_changeset(rev)

    def pull(self, url):
        """
        Tries to pull changes from external location.
        """
        url = self._get_url(url)
        try:
            pull(self.baseui, self.repo, url)
        except Abort, err:
            # Propagate error but with vcs's type
            raise RepositoryError(str(err))


class MercurialChangeset(BaseChangeset):
    """
    Represents state of the repository at the single revision.
    """

    def __init__(self, repository, revision):
        self.repository = repository
        revision = repository._get_revision(revision)
        try:
            ctx = repository.repo[revision]
        except RepoLookupError:
            raise RepositoryError("Cannot find revision %s" % revision)
        self.revision = ctx.rev()
        self._ctx = ctx
        self._fctx = {}
        self.author = safe_unicode(ctx.user())
        self.message = safe_unicode(ctx.description())
        self.branch = ctx.branch()
        self.tags = ctx.tags()
        self.date = date_fromtimestamp(*ctx.date())
        self.nodes = {}

    @LazyProperty
    def status(self):
        """
        Returns modified, added, removed, deleted files for current changeset
        """

        st1 = self.repository.repo.status(self._ctx.parents()[0], self._ctx)[:4]

#        if len(self._ctx.parents()) > 1:
#            st2 = self.repository.repo.status(self._ctx.parents()[1], self._ctx)[:4]
#            return map(lambda x: x[0] + x[1], zip(st1, st2))

        return st1


    @LazyProperty
    def _file_paths(self):
        return list(self._ctx)

    @LazyProperty
    def _dir_paths(self):
        p = list(set(get_dirs_for_path(*self._file_paths)))
        p.insert(0, '')
        return p

    @LazyProperty
    def _paths(self):
        return self._dir_paths + self._file_paths

    @LazyProperty
    def id(self):
        if self.last:
            return u'tip'
        return self.short_id

    @LazyProperty
    def raw_id(self):
        """
        Returns raw string identifying this changeset, useful for web
        representation.
        """
        return self._ctx.hex()

    @LazyProperty
    def short_id(self):
        return self.raw_id[:12]

    @LazyProperty
    def parents(self):
        """
        Returns list of parents changesets.
        """
        return [self.repository.get_changeset(parent.rev())
                for parent in self._ctx.parents() if parent.rev() >= 0]

    def _fix_path(self, path):
        """
        Paths are stored without trailing slash so we need to get rid off it if
        needed.
        """
        if path.endswith('/'):
            path = path.rstrip('/')
        return path

    def _get_kind(self, path):
        path = self._fix_path(path)
        if path in self._file_paths:
            return NodeKind.FILE
        elif path in self._dir_paths:
            return NodeKind.DIR
        else:
            raise ChangesetError("Node does not exist at the given path %r"
                % (path))

    def _get_filectx(self, path):
        if self._get_kind(path) != NodeKind.FILE:
            raise ChangesetError("File does not exist for revision %r at "
                " %r" % (self.revision, path))
        if not path in self._fctx:
            self._fctx[path] = self._ctx[path]
        return self._fctx[path]

    def get_file_content(self, path):
        """
        Returns content of the file at given ``path``.
        """
        fctx = self._get_filectx(path)
        return fctx.data()

    def get_file_size(self, path):
        """
        Returns size of the file at given ``path``.
        """
        fctx = self._get_filectx(path)
        return fctx.size()

    def get_file_changeset(self, path):
        """
        Returns last commit of the file at the given ``path``.
        """
        fctx = self._get_filectx(path)
        changeset = self.repository.get_changeset(fctx.linkrev())
        return changeset

    def get_file_history(self, path):
        """
        Returns history of file as reversed list of ``Changeset`` objects for
        which file at given ``path`` has been modified.
        """
        fctx = self._get_filectx(path)
        nodes = [fctx.filectx(x).node() for x in fctx.filelog()]
        changesets = [self.repository.get_changeset(hex(node))
            for node in reversed(nodes)]
        return changesets

    def get_file_annotate(self, path):
        """
        Returns a list of three element tuples with lineno,changeset and line
        """
        fctx = self._get_filectx(path)
        annotate = []
        for i, annotate_data in enumerate(fctx.annotate()):
            ln_no = i + 1
            annotate.append((ln_no, self.repository\
                             .get_changeset(hex(annotate_data[0].node())),
                             annotate_data[1],))

        return annotate

    def get_nodes(self, path):
        """
        Returns combined ``DirNode`` and ``FileNode`` objects list representing
        state of changeset at the given ``path``. If node at the given ``path``
        is not instance of ``DirNode``, ChangesetError would be raised.
        """

        if self._get_kind(path) != NodeKind.DIR:
            raise ChangesetError("Directory does not exist for revision %r at "
                " %r" % (self.revision, path))
        path = self._fix_path(path)
        filenodes = [FileNode(f, changeset=self) for f in self._file_paths
            if os.path.dirname(f) == path]
        dirs = path == '' and '' or [d for d in self._dir_paths
            if d and posixpath.dirname(d) == path]
        dirnodes = [DirNode(d, changeset=self) for d in dirs
            if os.path.dirname(d) == path]
        nodes = dirnodes + filenodes
        # cache nodes
        for node in nodes:
            self.nodes[node.path] = node
        nodes.sort()
        return nodes

    def get_node(self, path):
        """
        Returns ``Node`` object from the given ``path``. If there is no node at
        the given ``path``, ``ChangesetError`` would be raised.
        """
        if isinstance(path, unicode):
            path = path.encode('utf-8')

        path = self._fix_path(path)
        if not path in self.nodes:
            if path in self._file_paths:
                node = FileNode(path, changeset=self)
            elif path in self._dir_paths or path in self._dir_paths:
                if path == '':
                    node = RootNode(changeset=self)
                else:
                    node = DirNode(path, changeset=self)
            else:
                raise NodeDoesNotExistError("There is no file nor directory "
                    "at the given path: %r at revision %r"
                    % (path, '%s:%s' % (self.revision, self.id)))
            # cache node
            self.nodes[path] = node
        return self.nodes[path]

    @LazyProperty
    def _ppmp(self):
        """
        Helper cache function for getting manifest files used in added
        changed removed functions
        """
        p = self._ctx.parents()
        large_ = len(self.affected_files) > 100
        if large_:
            manifest = []
            parrent_manifest = []
        else:
            manifest = self._ctx.manifest()
            parrent_manifest = p[0].manifest()
        return p, self.affected_files, manifest, parrent_manifest, large_


    @LazyProperty
    def affected_files(self):
        """
        Get's a fast accessible file changes for given changeset
        """
        return self._ctx.files()

    @LazyProperty
    def added(self):
        """
        Returns list of added ``FileNode`` objects.
        """
        parents, paths, manifest, parent_manifest, large_ = self._ppmp
        #use status when this cs is a merge
        if len(parents) > 1 or large_:
            return AddedFileNodesGenerator([n for n in self.status[1]], self)

        added_nodes = []
        for path in paths:
            if not parent_manifest.has_key(path):
                added_nodes.append(path)

        return AddedFileNodesGenerator(added_nodes, self)


    @LazyProperty
    def changed(self):
        """
        Returns list of modified ``FileNode`` objects.
        """
        parents, paths, manifest, parent_manifest, large_ = self._ppmp
        #use status when this cs is a merge
        if len(parents) > 1 or large_:
            return ChangedFileNodesGenerator([ n for n in  self.status[0]], self)

        changed_nodes = []
        for path in paths:
            if manifest.has_key(path) and parent_manifest.has_key(path):
                changed_nodes.append(path)

        return ChangedFileNodesGenerator(changed_nodes, self)

    @LazyProperty
    def removed(self):
        """
        Returns list of removed ``FileNode`` objects.
        """
        parents, paths, manifest, parent_manifest, large_ = self._ppmp
        #use status when this cs is a merge
        if len(parents) > 1 or large_:
            rm_nodes = self.status[2] + self.status[3]
            return RemovedFileNodesGenerator([n for n in rm_nodes], self)

        removed_nodes = []
        for path in paths:
            if not manifest.has_key(path):
                removed_nodes.append(path)

        return RemovedFileNodesGenerator(removed_nodes, self)


class MercurialInMemoryChangeset(BaseInMemoryChangeset):

    def commit(self, message, author, **kwargs):
        author = safe_unicode(author)
        try:
            tip = self.repository.get_changeset()
        except RepositoryError:
            tip = None

        def filectxfn(repo, memctx, path):
            """
            Marks given path as added/changed/removed in a given repo. This is
            for internal mercurial commit function.
            """

            # check if this path is removed
            if path in (node.path for node in self.removed):
                # Raising exception is a way to mark node for removal
                raise IOError(errno.ENOENT, '%s is deleted' % path)

            # check if this path is added
            for node in self.added:
                if node.path == path:
                    return memfilectx(path=node.path,
                        data=node.content,
                        islink=False,
                        isexec=False,
                        copied=False)

            # or changed
            for node in self.changed:
                if node.path == path:
                    return memfilectx(path=node.path,
                        data=node.content,
                        islink=False,
                        isexec=False,
                        copied=False)

            raise RepositoryError("Given path haven't been marked as added,"
                "changed or removed (%s)" % path)

        parent1 = tip and tip._ctx.node() or None
        parent2 = None

        commit_ctx = memctx(repo=self.repository.repo,
            parents=(parent1, parent2),
            text='',
            files=self.get_paths(),
            filectxfn=filectxfn,
            user=author,
            date=kwargs.get('date', None),
            extra=kwargs)

        # injecting given repo params
        commit_ctx._text = message
        commit_ctx._user = author
        commit_ctx._date = kwargs.get('date', None)

        # TODO: Catch exceptions!
        self.repository.repo.commitctx(commit_ctx) # Returns mercurial node
        self._commit_ctx = commit_ctx # For reference

        # Update vcs repository object & recreate mercurial repo
        new_id = tip and self.repository.revisions[-1] + 1 or 0
        self.repository.revisions.append(new_id)
        self.repository._set_repo(create=False)
        self.repository.changesets.pop(None, None)
        self.repository.changesets.pop('tip', None)
        tip = self.repository.get_changeset()
        self.reset()
        return tip





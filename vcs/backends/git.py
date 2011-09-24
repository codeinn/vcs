# -*- coding: utf-8 -*-
"""
    vcs.backends.git
    ~~~~~~~~~~~~~~~~

    Git backend implementation.

    :created_on: Apr 8, 2010
    :copyright: (c) 2010-2011 by Marcin Kuzminski, Lukasz Balcerzak.
"""

import os
import re
import time
import datetime
import posixpath
from dulwich import objects
from dulwich.repo import Repo, NotGitRepository
from itertools import chain
from string import Template
from subprocess import Popen, PIPE
from vcs.backends.base import BaseChangeset
from vcs.backends.base import BaseInMemoryChangeset
from vcs.backends.base import BaseRepository
from vcs.backends.base import BaseWorkdir
from vcs.conf import settings
from vcs.exceptions import BranchDoesNotExistError
from vcs.exceptions import ChangesetDoesNotExistError
from vcs.exceptions import ChangesetError
from vcs.exceptions import EmptyRepositoryError
from vcs.exceptions import ImproperArchiveTypeError
from vcs.exceptions import NodeDoesNotExistError
from vcs.exceptions import RepositoryError
from vcs.exceptions import TagAlreadyExistError
from vcs.exceptions import TagDoesNotExistError
from vcs.exceptions import VCSError
from vcs.nodes import FileNode, DirNode, NodeKind, RootNode, RemovedFileNode
from vcs.utils import safe_unicode, makedate, date_fromtimestamp
from vcs.utils.lazy import LazyProperty
from vcs.utils.ordered_dict import OrderedDict
from vcs.utils.paths import abspath


class GitRepository(BaseRepository):
    """
    Git repository backend.
    """
    DEFAULT_BRANCH_NAME = 'master'
    scm = 'git'

    def __init__(self, repo_path, create=False, src_url=None,
                 update_after_clone=False):

        self.path = abspath(repo_path)
        self._repo = self._get_repo(create, src_url, update_after_clone)
        try:
            self.head = self._repo.head()
        except KeyError:
            self.head = None

    @LazyProperty
    def revisions(self):
        """
        Returns list of revisions' ids, in ascending order.  Being lazy
        attribute allows external tools to inject shas from cache.
        """
        return self._get_all_revisions()

    def run_git_command(self, cmd):
        """
        Runs given ``cmd`` as git command and returns tuple
        (returncode, stdout, stderr).

        .. note::
           This method exists only until log/blame functionality is implemented
           at Dulwich (see https://bugs.launchpad.net/bugs/645142). Parsing
           os command's output is road to hell...

        :param cmd: git command to be executed
        """
        #cmd = '(cd %s && git %s)' % (self.path, cmd)
        if isinstance(cmd, basestring):
            cmd = 'git %s' % cmd
        else:
            cmd = ['git'] + cmd
        try:
            opts = dict(
                shell=isinstance(cmd, basestring),
                stdout=PIPE,
                stderr=PIPE)
            if os.path.isdir(self.path):
                opts['cwd'] = self.path
            p = Popen(cmd, **opts)
        except OSError, err:
            raise RepositoryError("Couldn't run git command (%s).\n"
                "Original error was:%s" % (cmd, err))
        so, se = p.communicate()
        if not se.startswith("fatal: bad default revision 'HEAD'") and \
            p.returncode != 0:
            raise RepositoryError("Couldn't run git command (%s).\n"
                "stderr:\n%s" % (cmd, se))
        return so, se

    def _get_diff(self, rev1, rev2, path):
        cmd = 'diff %s %s %s' % (rev1, rev2, path)
        so, se = self.run_git_command(cmd)

        return so

    def _check_url(self, url):
        """
        Functon will check given url and try to verify if it's a valid
        link. Sometimes it may happened that mercurial will issue basic
        auth request that can cause whole API to hang when used from python
        or other external calls.

        On failures it'll raise urllib2.HTTPError
        """

        #TODO: implement this
        pass


    def _get_repo(self, create, src_url=None, update_after_clone=False):
        if create and os.path.exists(self.path):
            raise RepositoryError("Location already exist")
        if src_url and not create:
            raise RepositoryError("Create should be set to True if src_url is "
                                  "given (clone operation creates repository)")
        try:
            if create and src_url:
                self._check_url(src_url)
                self.clone(src_url, update_after_clone)
                return Repo(self.path)
            elif create:
                os.mkdir(self.path)
                return Repo.init(self.path)
            else:
                return Repo(self.path)
        except (NotGitRepository, OSError), err:
            raise RepositoryError(err)

    def _get_all_revisions(self):
        cmd = 'rev-list --all --date-order'
        try:
            so, se = self.run_git_command(cmd)
        except RepositoryError:
            # Can be raised for empty repositories
            return []
        revisions = so.splitlines()
        revisions.reverse()
        return revisions

    def _get_revision(self, revision):
        """
        For git backend we always return integer here. This way we ensure
        that changset's revision attribute would become integer.
        """
        pattern = re.compile(r'^[[0-9a-fA-F]{12}|[0-9a-fA-F]{40}]$')

        if len(self.revisions) == 0:
            raise EmptyRepositoryError("There are no changesets yet")

        if revision in (None, 'tip', 'HEAD', 'head', -1):
            revision = self.revisions[-1]

        if (isinstance(revision, (str, unicode)) and revision.isdigit() \
            and len(revision) < 12) or isinstance(revision, int):
            try:
                revision = self.revisions[int(revision)]
            except:
                raise ChangesetDoesNotExistError("Revision %r does not exist "
                    "for this repository %s" % (revision, self))

        elif isinstance(revision, (str, unicode)):
            if not pattern.match(revision) or revision not in self.revisions:
                raise ChangesetDoesNotExistError("Revision %r does not exist "
                    "for this repository %s" % (revision, self))

        # Ensure we return full id
        if not pattern.match(str(revision)):
            raise ChangesetDoesNotExistError("Given revision %r not recognized"
                % revision)
        return revision

    def _get_archives(self, archive_name='tip'):

        for i in [('zip', '.zip'), ('gz', '.tar.gz'), ('bz2', '.tar.bz2')]:
                yield {"type": i[0], "extension": i[1], "node": archive_name}

    def _get_url(self, url):
        """
        Returns normalized url. If schema is not given, would fall to
        filesystem (``file://``) schema.
        """
        url = str(url)
        if url != 'default' and not '://' in url:
            url = '://'.join(('file', url))
        return url

    @LazyProperty
    def name(self):
        return os.path.basename(self.path)

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
            in_path = os.path.join(self.path, '.git', "index")
            he_path = os.path.join(self.path, '.git', "HEAD")
            if os.path.exists(in_path):
                return os.stat(in_path).st_mtime
            else:
                return os.stat(he_path).st_mtime

    @LazyProperty
    def description(self):
        undefined_description = 'unknown'
        description_path = os.path.join(self.path, '.git', 'description')
        if os.path.isfile(description_path):
            return open(description_path).read()
        else:
            return undefined_description

    @LazyProperty
    def contact(self):
        undefined_contact = 'Unknown'
        return undefined_contact

    @property
    def branches(self):
        if not self.revisions:
            return {}
        refs = self._repo.refs.as_dict()
        sortkey = lambda ctx: ctx[0]
        _branches = [(ref.split('/')[-1], head)
            for ref, head in refs.items()
            if ref.startswith('refs/heads/') or
            ref.startswith('refs/remotes/') and not ref.endswith('/HEAD')]
        return OrderedDict(sorted(_branches, key=sortkey, reverse=False))

    def _get_tags(self):
        if not self.revisions:
            return {}
        sortkey = lambda ctx: ctx[0]
        _tags = [(ref.split('/')[-1], head,) for ref, head in
            self._repo.get_refs().items() if ref.startswith('refs/tags/')]
        return OrderedDict(sorted(_tags, key=sortkey, reverse=True))

    @LazyProperty
    def tags(self):
        return self._get_tags()

    def tag(self, name, user, revision=None, message=None, date=None,
            **kwargs):
        """
        Creates and returns a tag for the given ``revision``.

        :param name: name for new tag
        :param user: full username, i.e.: "Joe Doe <joe.doe@example.com>"
        :param revision: changeset id for which new tag would be created
        :param message: message of the tag's commit
        :param date: date of tag's commit

        :raises TagAlreadyExistError: if tag with same name already exists
        """
        if name in self.tags:
            raise TagAlreadyExistError("Tag %s already exists" % name)
        changeset = self.get_changeset(revision)
        message = message or "Added tag %s for commit %s" % (name,
            changeset.raw_id)
        self._repo.refs["refs/tags/%s" % name] = changeset._commit.id

        self.tags = self._get_tags()
        return changeset

    def remove_tag(self, name, user, message=None, date=None):
        """
        Removes tag with the given ``name``.

        :param name: name of the tag to be removed
        :param user: full username, i.e.: "Joe Doe <joe.doe@example.com>"
        :param message: message of the tag's removal commit
        :param date: date of tag's removal commit

        :raises TagDoesNotExistError: if tag with given name does not exists
        """
        if name not in self.tags:
            raise TagDoesNotExistError("Tag %s does not exist" % name)
        tagpath = posixpath.join(self._repo.refs.path, 'refs', 'tags', name)
        try:
            os.remove(tagpath)
            self.tags = self._get_tags()
        except OSError, e:
            raise RepositoryError(e.strerror)

    def get_changeset(self, revision=None):
        """
        Returns ``GitChangeset`` object representing commit from git repository
        at the given revision or head (most recent commit) if None given.
        """
        revision = self._get_revision(revision)
        changeset = GitChangeset(repository=self, revision=revision)
        return changeset

    def get_changesets(self, start=None, end=None, start_date=None,
           end_date=None, branch_name=None, reverse=False):
        """
        Returns iterator of ``GitChangeset`` objects from start to end (both
        are inclusive), in ascending date order (unless ``reverse`` is set).

        :param start: changeset ID, as str; first returned changeset
        :param end: changeset ID, as str; last returned changeset
        :param start_date: if specified, changesets with commit date less than
          ``start_date`` would be filtered out from returned set
        :param end_date: if specified, changesets with commit date greater than
          ``end_date`` would be filtered out from returned set
        :param branch_name: if specified, changesets not reachable from given
          branch would be filtered out from returned set
        :param reverse: if ``True``, returned generator would be reversed
          (meaning that returned changesets would have descending date order)

        :raise BranchDoesNotExistError: If given ``branch_name`` does not
            exist.
        :raise ChangesetDoesNotExistError: If changeset for given ``start`` or
          ``end`` could not be found.

        """
        if branch_name and branch_name not in self.branches:
            raise BranchDoesNotExistError("Branch '%s' not found" \
                                          % branch_name)
        # %H at format means (full) commit hash, initial hashes are retrieved
        # in ascending date order
        cmd_template = 'log --date-order --reverse --pretty=format:"%H"'
        cmd_params = {}
        if start_date:
            cmd_template += ' --since "$since"'
            cmd_params['since'] = start_date.strftime('%m/%d/%y %H:%M:%S')
        if end_date:
            cmd_template += ' --until "$until"'
            cmd_params['until'] = end_date.strftime('%m/%d/%y %H:%M:%S')
        if branch_name:
            cmd_template += ' $branch_name'
            cmd_params['branch_name'] = branch_name

        cmd = Template(cmd_template).safe_substitute(**cmd_params)
        revs = self.run_git_command(cmd)[0].splitlines()
        start_pos = 0
        end_pos = len(revs)
        if start:
            self._get_revision(start)
            try:
                start_pos = revs.index(start)
            except ValueError:
                pass
        if end:
            self._get_revision(end)
            try:
                end_pos = revs.index(end) + 1
            except ValueError:
                pass
        if (start_pos and end_pos) and start_pos > end_pos:
            raise RepositoryError('start cannot be after end')

        revs = revs[start_pos:end_pos]
        if reverse:
            revs = reversed(revs)
        for rev in revs:
            yield self.get_changeset(rev)

    @LazyProperty
    def in_memory_changeset(self):
        """
        Returns ``GitInMemoryChangeset`` object for this repository.
        """
        return GitInMemoryChangeset(self)

    def clone(self, url, update_after_clone):
        """
        Tries to clone changes from external location.
        if update_after_clone is set To false it'll prevent the runing update
        on workdir
        """
        url = self._get_url(url)
        cmd = 'clone '
        if not update_after_clone:
            cmd += '--no-checkout '
        cmd += '-- "%s" "%s"' % (url, self.path)
        # If error occurs run_git_command raises RepositoryError already
        self.run_git_command(cmd)

    @LazyProperty
    def workdir(self):
        """
        Returns ``Workdir`` instance for this repository.
        """
        return GitWorkdir(self)


class GitChangeset(BaseChangeset):
    """
    Represents state of the repository at single revision.
    """

    def __init__(self, repository, revision):
        self._stat_modes = {}
        self.repository = repository
        self.raw_id = revision
        self.revision = repository.revisions.index(revision)

        self.short_id = self.raw_id[:12]
        self.id = self.raw_id
        try:
            commit = self.repository._repo.get_object(self.raw_id)
        except KeyError:
            raise RepositoryError("Cannot get object with id %s" % self.raw_id)
        self._commit = commit
        self._tree_id = commit.tree

        try:
            self.message = safe_unicode(commit.message[:-1])
            # Always strip last eol
        except UnicodeDecodeError:
            self.message = commit.message[:-1].decode(commit.encoding
                or 'utf-8')
        #self.branch = None
        self.tags = []
        #tree = self.repository.get_object(self._tree_id)
        self.nodes = {}
        self._paths = {}

    @LazyProperty
    def author(self):
        return safe_unicode(self._commit.committer)

    @LazyProperty
    def date(self):
        return date_fromtimestamp(self._commit.commit_time,
                                  self._commit.commit_timezone)

    @LazyProperty
    def status(self):
        """
        Returns modified, added, removed, deleted files for current changeset
        """
        return self.changed, self.added, self.removed

    @LazyProperty
    def branch(self):
        # TODO: Cache as we walk (id <-> branch name mapping)
        refs = self.repository._repo.get_refs()
        heads = [(key[len('refs/heads/'):], val) for key, val in refs.items()
            if key.startswith('refs/heads/')]

        for name, id in heads:
            walker = self.repository._repo.object_store.get_graph_walker([id])
            while True:
                id = walker.next()
                if not id:
                    break
                if id == self.id:
                    return name
        raise ChangesetError("This should not happen... Have you manually "
            "change id of the changeset?")

    def _fix_path(self, path):
        """
        Paths are stored without trailing slash so we need to get rid off it if
        needed.
        """
        if path.endswith('/'):
            path = path.rstrip('/')
        return path

    def _get_id_for_path(self, path):
        # FIXME: Please, spare a couple of minutes and make those codes cleaner;
        if not path in self._paths:
            path = path.strip('/')
            # set root tree
            tree = self.repository._repo[self._commit.tree]
            if path == '':
                self._paths[''] = tree.id
                return tree.id
            splitted = path.split('/')
            dirs, name = splitted[:-1], splitted[-1]
            curdir = ''
            for dir in dirs:
                if curdir:
                    curdir = '/'.join((curdir, dir))
                else:
                    curdir = dir
                #if curdir in self._paths:
                    ## This path have been already traversed
                    ## Update tree and continue
                    #tree = self.repository._repo[self._paths[curdir]]
                    #continue
                dir_id = None
                for item, stat, id in tree.iteritems():
                    if curdir:
                        item_path = '/'.join((curdir, item))
                    else:
                        item_path = item
                    self._paths[item_path] = id
                    self._stat_modes[item_path] = stat
                    if dir == item:
                        dir_id = id
                if dir_id:
                    # Update tree
                    tree = self.repository._repo[dir_id]
                    if not isinstance(tree, objects.Tree):
                        raise ChangesetError('%s is not a directory' % curdir)
                else:
                    raise ChangesetError('%s have not been found' % curdir)
            for item, stat, id in tree.iteritems():
                if curdir:
                    name = '/'.join((curdir, item))
                else:
                    name = item
                self._paths[name] = id
                self._stat_modes[name] = stat
            if not path in self._paths:
                raise NodeDoesNotExistError("There is no file nor directory "
                    "at the given path %r at revision %r"
                    % (path, self.short_id))
        return self._paths[path]

    def _get_kind(self, path):
        id = self._get_id_for_path(path)
        obj = self.repository._repo[id]
        if isinstance(obj, objects.Blob):
            return NodeKind.FILE
        elif isinstance(obj, objects.Tree):
            return NodeKind.DIR

    def _get_file_nodes(self):
        return chain(*(t[2] for t in self.walk()))

    @LazyProperty
    def parents(self):
        """
        Returns list of parents changesets.
        """
        return [self.repository.get_changeset(parent)
            for parent in self._commit.parents]

    def next(self, branch=None):

        if branch and self.branch != branch:
            raise VCSError('Branch option used on changeset not belonging '
                           'to that branch')

        def _next(changeset, branch):
            try:
                next_ = changeset.revision + 1
                next_rev = changeset.repository.revisions[next_]
            except IndexError:
                raise ChangesetDoesNotExistError
            cs = changeset.repository.get_changeset(next_rev)

            if branch and branch != cs.branch:
                return _next(cs, branch)

            return cs

        return _next(self, branch)

    def prev(self, branch=None):
        if branch and self.branch != branch:
            raise VCSError('Branch option used on changeset not belonging '
                           'to that branch')

        def _prev(changeset, branch):
            try:
                prev_ = changeset.revision - 1
                if prev_ < 0:
                    raise IndexError
                prev_rev = changeset.repository.revisions[prev_]
            except IndexError:
                raise ChangesetDoesNotExistError

            cs = changeset.repository.get_changeset(prev_rev)

            if branch and branch != cs.branch:
                return _prev(cs, branch)

            return cs

        return _prev(self, branch)

    def get_file_mode(self, path):
        """
        Returns stat mode of the file at the given ``path``.
        """
        # ensure path is traversed
        self._get_id_for_path(path)
        return self._stat_modes[path]

    def get_file_content(self, path):
        """
        Returns content of the file at given ``path``.
        """
        id = self._get_id_for_path(path)
        blob = self.repository._repo[id]
        return blob.as_pretty_string()

    def get_file_size(self, path):
        """
        Returns size of the file at given ``path``.
        """
        id = self._get_id_for_path(path)
        blob = self.repository._repo[id]
        return blob.raw_length()

    def get_file_changeset(self, path):
        """
        Returns last commit of the file at the given ``path``.
        """
        node = self.get_node(path)
        return node.history[0]

    def get_file_history(self, path):
        """
        Returns history of file as reversed list of ``Changeset`` objects for
        which file at given ``path`` has been modified.

        TODO: This function now uses os underlying 'git' and 'grep' commands
        which is generally not good. Should be replaced with algorithm
        iterating commits.
        """
        cmd = 'log --name-status -p %s -- "%s" | grep "^commit"' \
            % (self.id, path)
        so, se = self.repository.run_git_command(cmd)
        ids = re.findall(r'\w{40}', so)
        return [self.repository.get_changeset(id) for id in ids]

    def get_file_annotate(self, path):
        """
        Returns a list of three element tuples with lineno,changeset and line

        TODO: This function now uses os underlying 'git' command which is
        generally not good. Should be replaced with algorithm iterating
        commits.
        """
        cmd = 'blame -l --root -r %s -- "%s"' % (self.id, path)
        # -l     ==> outputs long shas (and we need all 40 characters)
        # --root ==> doesn't put '^' character for bounderies
        # -r sha ==> blames for the given revision
        so, se = self.repository.run_git_command(cmd)
        annotate = []
        for i, blame_line in enumerate(so.split('\n')[:-1]):
            ln_no = i + 1
            id, line = re.split(r' \(.+?\) ', blame_line, 1)
            annotate.append((ln_no, self.repository.get_changeset(id), line))
        return annotate

    def fill_archive(self, stream=None, kind='tgz', prefix=None,
                     subrepos=False):
        """
        Fills up given stream.

        :param stream: file like object.
        :param kind: one of following: ``zip``, ``tgz`` or ``tbz2``.
            Default: ``tgz``.
        :param prefix: name of root directory in archive.
            Default is repository name and changeset's raw_id joined with dash
            (``repo-tip.<KIND>``).
        :param subrepos: include subrepos in this archive.
        
        :raise ImproperArchiveTypeError: If given kind is wrong.
        :raise VcsError: If given stream is None

        """
        allowed_kinds = settings.ARCHIVE_SPECS.keys()
        if kind not in allowed_kinds:
            raise ImproperArchiveTypeError('Archive kind not supported use one'
                'of %s', allowed_kinds)

        if prefix is None:
            prefix = '%s-%s' % (self.repository.name, self.short_id)
        elif prefix.startswith('/'):
            raise VCSError("Prefix cannot start with leading slash")
        elif prefix.strip() == '':
            raise VCSError("Prefix cannot be empty")

        if kind == 'zip':
            frmt = 'zip'
        else:
            frmt = 'tar'
        cmd = 'git archive --format=%s --prefix=%s/ %s' % (frmt, prefix,
            self.raw_id)
        if kind == 'tgz':
            cmd += ' | gzip -9'
        elif kind == 'tbz2':
            cmd += ' | bzip2 -9'

        if stream is None:
            raise VCSError('You need to pass in a valid stream for filling'
                           ' with archival data')
        else:
            arch_path = None

        popen = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True,
            cwd=self.repository.path)

        buffer_size = 1024 * 8
        chunk = popen.stdout.read(buffer_size)
        while chunk:
            stream.write(chunk)
            chunk = popen.stdout.read(buffer_size)
        # Make sure all descriptors would be read
        popen.communicate()

    def get_nodes(self, path):
        if self._get_kind(path) != NodeKind.DIR:
            raise ChangesetError("Directory does not exist for revision %r at "
                " %r" % (self.revision, path))
        path = self._fix_path(path)
        id = self._get_id_for_path(path)
        tree = self.repository._repo[id]
        dirnodes = []
        filenodes = []
        for name, stat, id in tree.iteritems():
            obj = self.repository._repo.get_object(id)
            if path != '':
                obj_path = '/'.join((path, name))
            else:
                obj_path = name
            if obj_path not in self._stat_modes:
                self._stat_modes[obj_path] = stat
            if isinstance(obj, objects.Tree):
                dirnodes.append(DirNode(obj_path, changeset=self))
            elif isinstance(obj, objects.Blob):
                filenodes.append(FileNode(obj_path, changeset=self, mode=stat))
            else:
                raise ChangesetError("Requested object should be Tree "
                                     "or Blob, is %r" % type(obj))
        nodes = dirnodes + filenodes
        for node in nodes:
            if not node.path in self.nodes:
                self.nodes[node.path] = node
        nodes.sort()
        return nodes

    def get_node(self, path):
        if isinstance(path, unicode):
            path = path.encode('utf-8')
        path = self._fix_path(path)
        if not path in self.nodes:
            try:
                id = self._get_id_for_path(path)
            except ChangesetError:
                raise NodeDoesNotExistError("Cannot find one of parents' "
                    "directories for a given path: %s" % path)
            obj = self.repository._repo.get_object(id)
            if isinstance(obj, objects.Tree):
                if path == '':
                    node = RootNode(changeset=self)
                else:
                    node = DirNode(path, changeset=self)
                node._tree = obj
            elif isinstance(obj, objects.Blob):
                node = FileNode(path, changeset=self)
                node._blob = obj
            else:
                raise NodeDoesNotExistError("There is no file nor directory "
                    "at the given path %r at revision %r"
                    % (path, self.short_id))
            # cache node
            self.nodes[path] = node
        return self.nodes[path]

    @LazyProperty
    def affected_files(self):
        """
        Get's a fast accessible file changes for given changeset
        """

        return self.added + self.changed

    @LazyProperty
    def _diff_name_status(self):
        output = []
        for parent in self.parents:
            cmd = 'diff --name-status %s %s' % (parent.raw_id, self.raw_id)
            so, se = self.repository.run_git_command(cmd)
            output.append(so.strip())
        return '\n'.join(output)

    def _get_paths_for_status(self, status):
        """
        Returns sorted list of paths for given ``status``.

        :param status: one of: *added*, *modified* or *deleted*
        """
        paths = set()
        char = status[0].upper()
        for line in self._diff_name_status.splitlines():
            if not line:
                continue
            if line.startswith(char):
                splitted = line.split()
                if not len(splitted) == 2:
                    raise VCSError("Couldn't parse diff result:\n%s\n\n and "
                        "particularly that line: %s" % (self._diff_name_status,
                        line))
                paths.add(splitted[1])
        return sorted(paths)

    @LazyProperty
    def added(self):
        """
        Returns list of added ``FileNode`` objects.
        """
        if not self.parents:
            return list(self._get_file_nodes())
        return [self.get_node(path) for path in self._get_paths_for_status('added')]

    @LazyProperty
    def changed(self):
        """
        Returns list of modified ``FileNode`` objects.
        """
        if not self.parents:
            return []
        return [self.get_node(path) for path in self._get_paths_for_status('modified')]

    @LazyProperty
    def removed(self):
        """
        Returns list of removed ``FileNode`` objects.
        """
        if not self.parents:
            return []
        return [RemovedFileNode(path) for path in self._get_paths_for_status('deleted')]


class GitInMemoryChangeset(BaseInMemoryChangeset):

    def commit(self, message, author, parents=None, branch=None, date=None,
            **kwargs):
        """
        Performs in-memory commit (doesn't check workdir in any way) and
        returns newly created ``Changeset``. Updates repository's
        ``revisions``.

        :param message: message of the commit
        :param author: full username, i.e. "Joe Doe <joe.doe@example.com>"
        :param parents: single parent or sequence of parents from which commit
          would be derieved
        :param date: ``datetime.datetime`` instance. Defaults to
          ``datetime.datetime.now()``.
        :param branch: branch name, as string. If none given, default backend's
          branch would be used.

        :raises ``CommitError``: if any error occurs while committing
        """
        self.check_integrity(parents)

        if branch is None:
            branch = GitRepository.DEFAULT_BRANCH_NAME

        repo = self.repository._repo
        object_store = repo.object_store

        ENCODING = "UTF-8"
        DIRMOD = 040000

        # Create tree and populates it with blobs
        commit_tree = self.parents[0] and repo[self.parents[0]._commit.tree] or\
            objects.Tree()
        for node in self.added + self.changed:
            # Compute subdirs if needed
            dirpath, nodename = posixpath.split(node.path)
            dirnames = dirpath and dirpath.split('/') or []
            parent = commit_tree
            ancestors = [('', parent)]

            # Tries to dig for the deepest existing tree
            while dirnames:
                curdir = dirnames.pop(0)
                try:
                    dir_id = parent[curdir][1]
                except KeyError:
                    # put curdir back into dirnames and stops
                    dirnames.insert(0, curdir)
                    break
                else:
                    # If found, updates parent
                    parent = self.repository._repo[dir_id]
                    ancestors.append((curdir, parent))
            # Now parent is deepest exising tree and we need to create subtrees
            # for dirnames (in reverse order) [this only applies for nodes from added]
            new_trees = []
            blob = objects.Blob.from_string(node.content.encode(ENCODING))
            node_path = node.name.encode(ENCODING)
            if dirnames:
                # If there are trees which should be created we need to build
                # them now (in reverse order)
                reversed_dirnames = list(reversed(dirnames))
                curtree = objects.Tree()
                curtree[node_path] = node.mode, blob.id
                new_trees.append(curtree)
                for dirname in reversed_dirnames[:-1]:
                    newtree = objects.Tree()
                    #newtree.add(DIRMOD, dirname, curtree.id)
                    newtree[dirname] = DIRMOD, curtree.id
                    new_trees.append(newtree)
                    curtree = newtree
                parent[reversed_dirnames[-1]] = DIRMOD, curtree.id
            else:
                parent.add(node.mode, node_path, blob.id)
            new_trees.append(parent)
            # Update ancestors
            for parent, tree, path in reversed([(a[1], b[1], b[0]) for a, b in
                zip(ancestors, ancestors[1:])]):
                parent[path] = DIRMOD, tree.id
                object_store.add_object(tree)

            object_store.add_object(blob)
            for tree in new_trees:
                object_store.add_object(tree)
        for node in self.removed:
            paths = node.path.split('/')
            tree = commit_tree
            trees = [tree]
            # Traverse deep into the forest...
            for path in paths:
                try:
                    obj = self.repository._repo[tree[path][1]]
                    if isinstance(obj, objects.Tree):
                        trees.append(obj)
                        tree = obj
                except KeyError:
                    break
            # Cut down the blob and all rotten trees on the way back...
            for path, tree in reversed(zip(paths, trees)):
                del tree[path]
                if tree:
                    # This tree still has elements - don't remove it or any
                    # of it's parents
                    break

        object_store.add_object(commit_tree)

        # Create commit
        commit = objects.Commit()
        commit.tree = commit_tree.id
        commit.parents = [p._commit.id for p in self.parents if p]
        commit.author = commit.committer = author
        commit.encoding = ENCODING
        commit.message = message + ' '

        # Compute date
        if date is None:
            date = time.time()
        elif isinstance(date, datetime.datetime):
            date = time.mktime(date.timetuple())

        author_time = kwargs.pop('author_time', date)
        commit.commit_time = int(date)
        commit.author_time = int(author_time)
        tz = time.timezone
        author_tz = kwargs.pop('author_timezone', tz)
        commit.commit_timezone = tz
        commit.author_timezone = author_tz

        object_store.add_object(commit)

        ref = 'refs/heads/%s' % branch
        repo.refs[ref] = commit.id
        repo.refs.set_symbolic_ref('HEAD', ref)

        # Update vcs repository object & recreate dulwich repo
        self.repository.revisions.append(commit.id)
        self.repository._repo = Repo(self.repository.path)
        tip = self.repository.get_changeset()
        self.reset()
        return tip

    def _get_missing_trees(self, path, root_tree):
        """
        Creates missing ``Tree`` objects for the given path.

        :param path: path given as a string. It may be a path to a file node
          (i.e. ``foo/bar/baz.txt``) or directory path - in that case it must
          end with slash (i.e. ``foo/bar/``).
        :param root_tree: ``dulwich.objects.Tree`` object from which we start
          traversing (should be commit's root tree)
        """
        dirpath = posixpath.split(path)[0]
        dirs = dirpath.split('/')
        if not dirs or dirs == ['']:
            return []

        def get_tree_for_dir(tree, dirname):
            for name, mode, id in tree.iteritems():
                if name == dirname:
                    obj = self.repository._repo[id]
                    if isinstance(obj, objects.Tree):
                        return obj
                    else:
                        raise RepositoryError("Cannot create directory %s "
                        "at tree %s as path is occupied and is not a "
                        "Tree" % (dirname, tree))
            return None

        trees = []
        parent = root_tree
        for dirname in dirs:
            tree = get_tree_for_dir(parent, dirname)
            if tree is None:
                tree = objects.Tree()
                dirmode = 040000
                parent.add(dirmode, dirname, tree.id)
                parent = tree
            # Always append tree
            trees.append(tree)
        return trees


class GitWorkdir(BaseWorkdir):

    def get_branch(self):
        headpath = self.repository._repo.refs.refpath('HEAD')
        try:
            content = open(headpath).read()
            match = re.match(r'^ref: refs/heads/(?P<branch>.+)\n$', content)
            if match:
                return match.groupdict()['branch']
            else:
                raise RepositoryError("Couldn't compute workdir's branch")
        except IOError:
            # Try naive way...
            raise RepositoryError("Couldn't compute workdir's branch")

    def get_changeset(self):
        return self.repository.get_changeset(
            self.repository._repo.refs.as_dict().get('HEAD'))

    def checkout_branch(self, branch=None):
        if branch is None:
            branch = self.repository.DEFAULT_BRANCH_NAME
        if branch not in self.repository.branches:
            raise BranchDoesNotExistError
        self.repository.run_git_command(['checkout', branch])


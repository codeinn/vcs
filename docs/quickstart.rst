.. _quickstart:

Quickstart
==========

Say you don't want to install ``vcs`` or just want to begin with really fast
tutorial?  Not a problem, just follow sections below.

Prepere
-------

We will try to show you how you can use ``vcs`` directly on repository. But hey,
``vcs`` is maintained within mercurial
`repository <http:http://bitbucket.org/marcinkuzminski/vcs/>`_ already, so why
not use it? Simply run following commands in your shell

.. code-block:: bash

   cd /tmp
   hg clone http://bitbucket.org/marcinkuzminski/vcs/
   cd vcs

Now run your python interpreter of choice::

   $ python
   >>>

.. note::
   You may of course put your clone of ``vcs`` wherever you like but running
   python shell *inside* of it would allow you to use just cloned version of
   ``vcs``.

Take the shortcut
-----------------

There is no need to import everything from ``vcs`` - in fact, all you'd need is
to import ``get_repo``, at least for now. Then, simply initialize repository
object by providing it's type and path.

.. code-block:: pycon

   >>> from vcs import get_repo
   >>>
   >>> # create mercurial repository representation at current dir
   >>> # alias tells which backend should be used (see vcs.BACKENDS)
   >>> repo = get_repo(alias='hg', path='.')

Basics
------

Let's ask repo about the content...

.. code-block:: python

   >>> root = repo.request('')
   >>> print root.nodes # prints nodes of the RootNode
   [<DirNode ''>, <DirNode 'docs'>, <DirNode 'tests'>, # ... (chopped)
   >>>
   >>> # get 10th changeset
   >>> chset = repo.get_changeset(10)
   >>> print chset
   <MercurialChangeset at 10>
   >>>
   >>> # any backend would return latest changeset if revision is not given
   >>> tip = repo.get_changeset()
   >>> tip is repo.get_changeset('tip') # for mercurial backend 'tip' is allowed
   True
   >>> tip is repo.get_changeset(None) # any backend allow revision to be None (default)
   True
   >>> tip.revision is repo.revisions[-1]
   True
   >>>
   >>> # Iterate repository
   >>> list(repo) == repo.changesets.values()
   False
   >>> # Those are not equal, as repo iterator returns only changesets for keys
   >>> # from repo.revisions and repo.changesets is a dict caching calls for
   >>> # each changeset; but repo iterator would always be a subset of cached
   >>> # changesets
   >>> set(list(repo)).issubset(set(repo.changesets.values()))
   True
   
Walking
-------

Now let's ask for nodes at revision 44
(http://bitbucket.org/marcinkuzminski/vcs/src/a0eada0b9e4e/)

.. code-block:: python

   >>> chset44 = repo.get_changeset(44)
   >>> root = chset44.root
   >>> # You may also use shorter one-liner:
   >>> root = repo.request('', 44)

.. note::
   If you have to check this to believe, you may get raw id of the changeset and
   open browser on same changeset at bitbucket::

      >>> print root.changeset.raw_id
      a0eada0b9e4e

   This show us that 44 revision has hex of (shorter version): ``a0eada0b9e4e``
   which you can follow on bitbucket at:
   http://bitbucket.org/marcinkuzminski/vcs/src/a0eada0b9e4e/

.. code-block:: python

   >>> print root.dirs
   [<DirNode 'docs'>, <DirNode 'examples'>, <DirNode 'tests'>, <DirNode 'vcs'>]

.. note::
   :ref:`api-nodes` are objects representing files and directories within the
   repository revision.

.. code-block:: python

   >>> # Fetch vcs directory
   >>> vcs = repo.request('vcs', 44)
   >>> print vcs.dirs
   [<DirNode 'vcs/backends'>, <DirNode 'vcs/utils'>, <DirNode 'vcs/web'>]
   >>> web_node = vcs.dirs[-1]
   >>> web = repo.request(web_node.path, 44)
   >>> print web.nodes
   [<DirNode 'vcs/web/simplevcs'>, <FileNode 'vcs/web/__init__.py'>]
   >>> print web.files
   [<FileNode 'vcs/web/__init__.py'>]
   >>> web.files[0].content
   ''
   >>> print vcs.files[0].content
   """
   Various Version Control System management abstraction layer for Python.
   """
   
   VERSION = (0, 0, 1, 'alpha')
   
   __version__ = '.'.join((str(each) for each in VERSION[:4]))
   
   __all__ = [
       'get_repo', 'get_backend', 'BACKENDS',
       'VCSError', 'RepositoryError', 'ChangesetError']
   
   from vcs.backends import get_repo, get_backend, BACKENDS
   from vcs.exceptions import VCSError, RepositoryError, ChangesetError
   

   >>> chset44 = repo.get_changeset(44)
   >>> chset44.get_node('vcs/web') is web
   True
   >>> # same if we span ``get_node`` methods:
   >>> chset44.get_node('vcs').get_node('web') is web
   True

Getting meta data
-----------------

Make ``vcs`` show us some meta information

Tags and branches
~~~~~~~~~~~~~~~~~

.. code-block:: python
   
   >>> [changeset.branch for changeset in repo.branches]
   ['default', 'web']
   >>> [changeset.tags for changeset in repo.tags]
   [['tip']]
   >>> # get changeset we know well
   >>> chset44 = repo.get_changeset(44)
   >>> chset44.branch
   'web'
   >>> chset44.tags
   []

Give me a file, finally!
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   >>> root = repo.request('', 44)
   >>> backends = root.get_node('vcs/backends')
   >>> backends.files
   [<FileNode 'vcs/backends/__init__.py'>,
    <FileNode 'vcs/backends/base.py'>,
    <FileNode 'vcs/backends/hg.py'>]
   >>> f = backends.get_node('hg.py')
   >>> f.name
   'hg.py'
   >>> f.path
   'vcs/backends/hg.py'
   >>> f.size
   8882
   >>> f.last_changeset
   <MercurialChangeset at 44>
   >>> f.last_changeset.date
   datetime.datetime(2010, 4, 14, 14, 8)
   >>> f.last_changeset.message
   'Cleaning up codes at base/mercurial backend'
   >>> f.last_changeset.author
   'Lukasz Balcerzak <lukasz.balcerzak@python-center.pl>'
   >>>
   >>> f.mimetype
   'text/x-python'
   >>>
   >>> # Following would raise exception unless you have pygments installed
   >>> f.lexer
   <pygments.lexers.PythonLexer>
   >>> f.lexer_alias # shortcut to get first of lexers' available aliases
   'python'
   >>> f.name
   'hg.py'
   >>>
   >>> # wanna go back? why? oh, whatever...
   >>> f.parent
   <DirNode 'vcs/backends'>
   >>>
   >>> # is it cached? hell yeah...
   >>> f is f.parent.get_node('hg.py') is repo.request('vcs/backends/hg.py', 44)
   True

How about history?
~~~~~~~~~~~~~~~~~~

.. versionadded:: 0.1.1

It is possible to retrieve changesets for which file node has been changed and
this is pretty damn simple. Let's say we want to see history of the file located
at ``vcs/nodes.py``.

.. code-block:: python

   >>> f = repo.request('vcs/nodes.py')
   >>> print f.history
   [<MercurialChangeset at 82>, <MercurialChangeset at 81>, <MercurialChange
   ...

Note that ``history`` attribute is computed lazily and returned list is reversed
- changesets are retrieved from most recent to oldest.

Show me the difference!
~~~~~~~~~~~~~~~~~~~~~~~

Here we present naive implementation of diff table for the given file node
located at ``vcs/nodes.py``. First we have to get the node from repository.
After that we retrieve last changeset for which the file has been modified
and we create a html file using `difflib`_.

.. code-block:: python

   >>> f = repo.request('vcs/nodes.py', 82)
   >>> f_old = repo.request(f.path, 81)
   >>> out = open('out.html', 'w')
   >>> from difflib import HtmlDiff
   >>> hd = HtmlDiff(tabsize=4)
   >>> diffs = hd.make_file(f.content.split('\n'), f_old.content.split('\n'))
   >>> out.write(diffs)
   >>> out.close()

.. _difflib: http://docs.python.org/library/difflib.html


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
   hg update web # temporary, new parts haven't yet landed into default branch
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
   >>> repo = get_repo(type='hg', path='.')

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
   >>> tip is repo['tip'] # for mercurial backend 'tip' is allowed
   True
   >>> tip is repo[None] # any backend allow revision to be None (default)
   True
   >>> tip.revision is repo.revisions[-1]
   True
   >>>
   >>> # Iterate repository
   >>> list(repo) == repo.changesets.values()
   True
   
Walking
-------

Now let's ask for nodes at revision 44
(http://bitbucket.org/marcinkuzminski/vcs/src/a0eada0b9e4e/)

.. code-block:: python

   >>> root = repo.request('', 44)
   >>> print root.dirs
   [<DirNode 'docs'>, <DirNode 'tests'>, <DirNode 'vcs'>]

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
   >>>
   >>> chset44 = repo[44]
   >>> chset44['vcs/web'] is web
   True

Getting meta data
-----------------

Make ``vcs`` show us some meta information

Tags and branches
~~~~~~~~~~~~~~~~~

.. code-block:: python
   
   >>> # get changeset we know well
   >>> chset44 = repo[44]
   >>> chset44.tags # most probably empty list after commit
   []
   >>> chset44.branches
   ['default', 'web']


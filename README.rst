===
VCS
===

various version control system management abstraction layer for python.

------------
Introduction
------------

``vcs`` is abstraction layer over various version control systems. It is
designed as feature-rich Python_ library with clean *API*.

vcs uses [Semantic Versioning](http://semver.org/)
 

.. note::
   Currently only Mercurial_ backend is being developed. Git_ is going to be
   second backend.

**Features**

- Common *API* for SCM backends
- Fetching repositories data lazily
- Simple caching mechanism so we don't hit repo too often

**Incoming**

- Django_ app for mercurial_ hgserve replacement
- Command line client
- Simple commit api
- Smart and powerfull in memory Workdirs
- Vcs based wiki

-------------
Documentation
-------------

Online documentation for development version is available at
http://packages.python.org/vcs/.

You may also build documentation for yourself - go into ``docs/`` and run::

   make html

.. _python: http://www.python.org/
.. _Django: http://www.djangoproject.com/
.. _Sphinx: http://sphinx.pocoo.org/
.. _mercurial: http://mercurial.selenic.com/
.. _git: http://git-scm.com/


.. _index:

Welcome to vcs's documentation!
===============================

``vcs`` is abstraction layer over various version control systems. It is
designed as feature-rich Python_ library with clear :ref:`API`. 

.. note::
   Currently only Mercurial_ backend is being developed. Git_ is going to be
   second backend.

**Features**

- Common :ref:`API` for SCM backends
- Fetching repositories data lazily
- Simple caching mechanism so we don't hit repo too often

**Incoming**

- Django_ app for mercurial_ hgserve replacement
- Command line client

Documentation
=============

**Installation:**

.. toctree::
   :maxdepth: 1

   quickstart
   installation
   api/index

Other topics
============

* :ref:`genindex`
* :ref:`search`

.. _python: http://www.python.org/
.. _django: http://www.djangoproject.com/
.. _mercurial: http://mercurial.selenic.com/
.. _subversion: http://subversion.tigris.org/
.. _git: http://git-scm.com/

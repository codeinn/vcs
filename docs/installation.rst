.. _installation:

Installation
============

``vcs`` is simply, pure python package. However, it makes use of various
*version control systems* and thus, would require some third part libraries
and they may have some deeper dependencies.

Requirements
------------

Below is a table which shows requirements for each backend.

+------------+--------------------+--------+-------------------+
| SCM        | Backend            | Alias  | Requirements      |
+============+====================+========+===================+
| Mercurial_ | ``vcs.backend.hg`` | ``hg`` | mercurial_ >= 1.5 |
+------------+--------------------+--------+-------------------+

.. _mercurial: http://mercurial.selenic.com/

Install from Cheese Shop
------------------------

Easiest way to install ``vcs`` is to run::

   easy_install vcs

Or::

   pip install vcs

If you prefer to install manually simply grab latest release from
http://pypi.python.org/pypi/vcs, decompress archive and run::

   python setup.py install

Development
-----------

In order to test the package you'd need all backends underlying libraries (see
table above) and nose_ as we use it to run test suites. Moreover, as ``vcs``
comes with some extra packages (i.e. ``vcs.web.simplevcs``) which relies on
external packages you'd need them too.

Here is a full list of packages needed to run test suite:

+-----------+---------------------------------------+
| Package   | Homepage                              |
+===========+=======================================+
| nose      | http://code.google.com/p/python-nose/ |
+-----------+---------------------------------------+
| mercurial | http://mercurial.selenic.com/         |
+-----------+---------------------------------------+
| django    | http://www.djangoproject.com/         |
+-----------+---------------------------------------+


.. _nose: http://code.google.com/p/python-nose/


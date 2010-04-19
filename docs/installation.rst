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

Development
-----------

In order to test the package you'd need all backends underlying libraries (see
table above) and nose_ as we use it to run test suites.

.. _nose: http://code.google.com/p/python-nose/


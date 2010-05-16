.. _api-backends-hg:

Mercurial Backend
=================

.. automodule:: vcs.backends.hg

MercurialRepository
-------------------

.. autoclass:: vcs.backends.hg.MercurialRepository
   :members:

MercurialChangeset
------------------

.. autoclass:: vcs.backends.hg.MercurialChangeset
   :members:
   :inherited-members:
   :undoc-members:
   :show-inheritance:

   .. autoattribute:: id

      Returns shorter version of mercurial's changeset hexes.

   .. autoattribute:: raw_id

      Returns raw string identifing this changeset, useful for web
      representation.

   .. autoattribute:: parents

      Returns list of parents changesets.

   .. autoattribute:: added

      Returns list of added ``FileNode`` objects.

   .. autoattribute:: changed 

      Returns list of changed ``FileNode`` objects.

   .. autoattribute:: removed 

      Returns list of removed ``RemovedFileNode`` objects.

      .. note::
         Remember that those ``RemovedFileNode`` instances are only dummy
         ``FileNode`` objects and trying to access most of it's attributes or
         methods would raise ``NodeError`` exception.


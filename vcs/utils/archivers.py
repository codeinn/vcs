# -*- coding: utf-8 -*-


class BaseArchiver(object):

    def __init__(self):
        self.archive_file = self._get_archive_file()

    def addfile(self):
        """
        Adds a file to archive container
        """
        pass

    def close(self):
        """
        Closes and finalizes operation of archive container object
        """
        self.archive_file.close()

    def _get_archive_file(self):
        """
        Returns container for specific archive
        """
        raise NotImplementedError()


class TarArchiver(BaseArchiver):
    pass


class Tbz2Archiver(BaseArchiver):
    pass


class TgzArchiver(BaseArchiver):
    pass


class ZipArchiver(BaseArchiver):
    pass


def get_archiver(self, kind):
    """
    Returns instance of archiver class specific to given kind

    :param kind: archive kind
    """

    archivers = {
        'tar': TarArchiver,
        'tbz2': Tbz2Archiver,
        'tgz': TgzArchiver,
        'zip': ZipArchiver,
    }

    return archivers[kind]()

def filesizeformat(bytes, sep=' '):
    """
    Formats the value like a 'human-readable' file size (i.e. 13 KB, 4.1 MB,
    102 B, 2.3 GB etc).

    Grabbed from Django (http://www.djangoproject.com), slightly modified.

    :param bytes: size in bytes (as integer)
    :param sep: string separator between number and abbreviation
    """
    try:
        bytes = float(bytes)
    except (TypeError, ValueError, UnicodeDecodeError):
        bytes = 0
        template = u'{size}{sep}B'
        formats = {'size': 0, 'sep': sep}
        return template.format(**formats)

    if bytes < 1024:
        return '{size:.0f}{sep}B'.format(size=bytes, sep=sep)
    if bytes < 1024 * 1024:
        return '{size:.0f}{sep}KB'.format(size=bytes / 1024, sep=sep)
    if bytes < 1024 * 1024 * 1024:
        return '{size:.1f}{sep}MB'.format(size=bytes / 1024 / 1024, sep=sep)
    return '{size:.2f}{sep}GB'.format(size=bytes / 1024 / 1024 / 1024, sep=sep)


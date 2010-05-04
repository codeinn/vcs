from difflib import unified_diff

def get_udiff(content1, content2):
    """
    Returns unified diff between given ``content1`` and ``content2``.
    """
    _udiff = unified_diff(content1.splitlines(True), content2.splitlines(True))
    udiff = ''.join(_udiff)
    return udiff


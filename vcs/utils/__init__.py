"""
This module provides some useful tools for ``vcs`` like annotate/diff html
output. It also includes some internal helpers.
"""

import time
def makedate():
    lt = time.localtime()
    if lt[8] == 1 and time.daylight:
        tz = time.altzone
    else:
        tz = time.timezone
    return time.mktime(lt), tz
import sys

if sys.version_info < (3, 6):
    raise ImportError("Python 3.6 or greater required.")
else:
    del sys

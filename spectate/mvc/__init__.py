"""
MVC
===

.. automodule:: spectate.mvc.base
    :members:

.. automodule:: spectate.mvc.models
    :members:

.. automodule:: spectate.mvc.utils
    :members:
"""

import sys

if sys.version_info < (3, 6):
    raise RuntimeError('Python 3.6 or greater required.')
else:
    del sys

from .base import *
from .models import *

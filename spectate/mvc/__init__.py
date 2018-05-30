"""
MVC
===

.. automodule:: spectate.mvc.base
    :members:
    :ignore-module-all:

.. automodule:: spectate.mvc.models
    :members:
    :ignore-module-all:

.. automodule:: spectate.mvc.utils
    :members:
"""

import sys

if sys.version_info < (3, 6):
    raise ImportError('Python 3.6 or greater required.')
else:
    del sys

from .base import *
from .models import *

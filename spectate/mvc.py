import sys

if sys.version_info < (3, 6):
    raise ImportError("Python 3.6 or greater required.")
else:
    del sys
"""A modules which exports specate's Model-View-Controller utilities in a common namespace

For more info:

- :mod:`spectate.base`
- :mod:`spectate.events`
- :mod:`spectate.models`
"""

from .base import *  # noqa
from .events import *  # noqa
from .models import *  # noqa

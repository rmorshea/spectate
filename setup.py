from __future__ import print_function
from setuptools import find_packages

# the name of the project
name = "spectate"

#-----------------------------------------------------------------------------
# Minimal Python version sanity check
#-----------------------------------------------------------------------------

import sys

v = sys.version_info
if v[:2] < (2,7) or (v[0] >= 3 and v[:2] < (3,3)):
    error = "ERROR: %s requires Python version 2.7 or 3.3 or above." % name
    print(error, file=sys.stderr)
    sys.exit(1)

#-----------------------------------------------------------------------------
# get on with it
#-----------------------------------------------------------------------------

import os
from glob import glob

from distutils.core import setup

here = os.path.abspath(os.path.dirname(__file__))
root = os.path.join(here, name)

packages = find_packages()

with open(os.path.join(root, '_version.py')) as f:
    namespace = {}
    exec(f.read(), {}, namespace)
    version = namespace["__version__"]

long_description = """
Spectate
========
Create classes whose instances have tracked methods

``spectate`` is useful for remotely tracking how an instance is modified. This means that protocols
for managing updates, don't need to be the outward responsibility of a user, and can instead be
done automagically in the background.

For example, if it were desirable to keep track of element changes in a list, ``spectate`` could be
used to observe ``list.__setitiem__`` in order to be notified when a user sets the value of an element
in the list. To do this, we would first create an ``elist`` type using ``expose_as``, construct an
instance of that type, and then store callback pairs to that instance's spectator. To access a spectator,
register one with ``watch`` (e.g. ``spectator = watch(the_elist)``), retrieve a preexisting one with the
``watcher`` function. Callback pairs are stored by calling the ``watcher(the_list).callback`` method. You
can then specify, with keywords, whether the callback should be triggered ``before``, and/or or ``after``
a given method is called - hereafter refered to as "beforebacks" and "afterbacks" respectively.
"""

setup_args = dict(
	name = name,
    version = version,
    packages = packages,
    description = "Create classes whose instances have tracked methods",
    long_description = long_description,
    author = "Ryan Morshead",
    author_email = "ryan.morshead@gmail.com",
    url = "https://github.com/rmorshea/spectate",
    license = 'MIT',
    platforms = "Linux, Mac OS X, Windows",
    keywords = ["eventful", "callbacks"],
    classifiers = [
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        ],
)

if __name__ == '__main__':
    setup(**setup_args)

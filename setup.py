from __future__ import print_function

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

PY3 = (sys.version_info[0] >= 3)

#-----------------------------------------------------------------------------
# get on with it
#-----------------------------------------------------------------------------

import os
from glob import glob

from distutils.core import setup

pjoin = os.path.join
here = os.path.abspath(os.path.dirname(__file__))
pkg_root = pjoin(here, name)

packages = []
for d, _, _ in os.walk(pjoin(here, name)):
    if os.path.exists(pjoin(d, '__init__.py')):
        packages.append(d[len(here)+1:].replace(os.path.sep, '.'))

version_ns = {}
with open(pjoin(here, name, '_version.py')) as f:
    exec(f.read(), {}, version_ns)

with open("summary.rst", "r") as f:
	long_description = f.read()

setup_args = dict(
	name = name,
    version = version_ns['__version__'],
    scripts = glob(pjoin('scripts', '*')),
    packages = packages,
    description = "Create classes whose instances have tracked methods",
    long_description = long_description,
    author = "Ryan Morshead",
    author_email = "ryan.morshead@gmail.com",
    url = "https://github.com/rmorshea/dstruct",
    license = 'MIT',
    platforms = "Linux, Mac OS X, Windows",
    keywords = ["spectate", "instance", "changes", "wrapper"],
    classifiers = [
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        ],
)

if __name__ == '__main__':
    setup(**setup_args)

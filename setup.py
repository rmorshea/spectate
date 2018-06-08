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


requirements = [
    'six',
]


with open(os.path.join(root, '_version.py')) as f:
    namespace = {}
    exec(f.read(), {}, namespace)
    version = namespace["__version__"]


with open(os.path.join(here, 'README.md')) as f:
    long_description = f.read()


if __name__ == '__main__':
    setup(
        name=name,
        version=version,
        packages=packages,
        description="Create classes whose instances have tracked methods",
        long_description=long_description,
        long_description_content_type='text/markdown',
        author="Ryan Morshead",
        author_email="ryan.morshead@gmail.com",
        url="https://github.com/rmorshea/spectate",
        license='MIT',
        platforms="Linux, Mac OS X, Windows",
        keywords=["eventful", "callbacks"],
        install_requires=requirements,
        classifiers=[
            'Intended Audience :: Developers',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3.3',
            ],
    )

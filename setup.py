import os
import sys
from setuptools import find_packages
from distutils.core import setup

name = "spectate"

# paths used to gather files
here = os.path.abspath(os.path.dirname(__file__))
pkg_root = os.path.join(here, name)

# -----------------------------------------------------------------------------
# Package Basics
# -----------------------------------------------------------------------------

package = dict(
    name=name,
    license="MIT",
    packages=find_packages(exclude=["tests"]),
    python_requires=">=3.6",
    description="Track changes to mutable data types.",
    classifiers=["Intended Audience :: Developers"],
    author="Ryan Morshead",
    author_email="ryan.morshead@gmail.com",
    url="https://github.com/rmorshea/spectate",
    keywords=["eventful", "callbacks", "mutable", "MVC", "model", "view", "controller"],
    platforms="Linux, Mac OS X, Windows",
    include_package_data=True,
)

# -----------------------------------------------------------------------------
# Library Version
# -----------------------------------------------------------------------------

with open(os.path.join(pkg_root, "__init__.py")) as f:
    for line in f.read().split("\n"):
        if line.startswith("__version__ = "):
            package["version"] = eval(line.split("=", 1)[1])
            break
    else:
        print("No version found in %s/__init__.py" % pkg_root)
        sys.exit(1)

# -----------------------------------------------------------------------------
# Library Description
# -----------------------------------------------------------------------------

package["long_description_content_type"] = "text/markdown"
with open(os.path.join(here, "README.md")) as f:
    package["long_description"] = f.read()

# -----------------------------------------------------------------------------
# Install It
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    setup(**package)

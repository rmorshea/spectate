[![Build Status](https://travis-ci.org/rmorshea/spectate.svg?branch=master)](https://travis-ci.org/rmorshea/spectate/branches)
[![Documentation Status](https://readthedocs.org/projects/python-spectate/badge/?version=latest)](http://python-spectate.readthedocs.io/en/latest/?badge=latest)
[![Version Info](https://img.shields.io/pypi/v/spectate.svg)](https://pypi.python.org/pypi/spectate)

# Spectate

A library for Python 2 and 3 that can track changes to mutable data types.

With `spectate` complicated protocols for managing updates, don't need to be the outward responsibility of a user, and can instead be done automagically in the background. For instance, syncing the state between a server and client can controlled by `spectate` so user's don't have to.


# Documentation

https://python-spectate.readthedocs.io/en/latest/


# Install

+ stable

```bash
pip install spectate
```

+ pre-release

```bash
pip install spectate --pre
```

+ master

```bash
pip install git+https://github.com/rmorshea/spectate.git#egg=spectate
```

+ developer

```bash
git clone https://github.com/rmorshea/spectate && cd spectate/ && pip install -e . -r requirements.txt
```


# At A Glance

If you're using Python 3.6 and above, create a model object

```python
from spectate import mvc

l = mvc.List()
```

Register a view function to it that observes changes

```python
@mvc.view(l)
def printer(l, events):
    for e in events:
        print(e)
```

Then modify your object and watch the view function react

```python
l.append(0)
l[0] = 1
l.extend([2, 3])
```

```
{'index': 0, 'old': Undefined, 'new': 0}
{'index': 0, 'old': 0, 'new': 1}
{'index': 1, 'old': Undefined, 'new': 2}
{'index': 2, 'old': Undefined, 'new': 3}
```

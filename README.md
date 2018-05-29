[![Build Status](https://travis-ci.org/rmorshea/spectate.svg)](https://travis-ci.org/rmorshea/spectate)
[![Documentation Status](https://readthedocs.org/projects/python-spectate/badge/?version=latest)](http://python-spectate.readthedocs.io/en/latest/?badge=latest)
[![Version Info](https://img.shields.io/pypi/v/spectate.svg)](https://pypi.python.org/pypi/spectate)


# Spectate

A library for Python 2 and 3 that can track changes to mutable data types.

With `spectate` complicated protocols for managing updates, don't need to be the outward responsibility of a user, and can instead be done automagically in the background. For instance, syncing the state between a server and client can controlled by `spectate` so user's don't have to.


# Install

+ stable : `pip install spectate`
+ master : `pip install git+https://github.com/rmorshea/spectate.git#egg=spectate`
+ developer : `git clone https://github.com/rmorshea/spectate && cd spectate/ && pip install -e . -r requirements.txt`


# Usage

```python
from spectate import expose, watch
```

Expose any desired method of a class so it can be watched.

```python
@expose('increment', 'decrement')
class Counter(object):

    def __init__(self):
        self.x = 0

    def increment(self, amount):
        self.x += amount

    def decrement(self, amount):
        self.x -= amount
```

Create an instance of the new watchable class, and get its spectator.

```python
counter = Counter()
spectator = watch(counter)
```

Register a callback to the methods you exposed.

```python
def changed(counter, answer):
    print(counter.x)

spectator.callback('increment', after=changed)
spectator.callback('decrement', after=changed)
```

Normal usage of the exposed methods will trigger your callback.

```python
counter.increment(1)
counter.decrement(2)
counter.increment(3)
counter.decrement(4)
```

And thus print out the following:

```
1
-1
2
-2
```

[... see more examples. ](https://github.com/rmorshea/spectate/tree/master/examples)


## Kinds of Callbacks

Callbacks are registered to specific methods in pairs - one will be triggered before, and the other after, a call to that method is made. These two callbacks are referred to as "beforebacks" and "afterbacks" respectively. Defining both a beforeback and an afterback in each pair is not required, but doing so allows a beforeback to pass data to its corresponding afterback.


### Beforebacks

Have a signature of `(instance, call)`

+ `instance` is the owner of the method
+ `call` is a `dict` with the keys
    + `'name'` - the name of the method which was called
    + `'args'` - the arguments which that method will call
    + `'kwargs'` - the keywords which that method will call
+ Can `return` a value which gets passed on to its respective afterback, or a [Closure](#Closure) that itself gets treated as an afterback.


### Afterbacks

Have a signature of `(instance, answer)`

+ `instance` is the owner of the method
+ `answer` is a `dict` with the keys
    + `'name'` - the name of the method which was called
    + `'value'` - the value returned by the method
    + `'before'` - the value returned by the respective beforeback


### Closures

Have a signature of `(value)`

+ `'value'` - the value returned by the method
+ All other information is already contained in the closures scope.
+ Should not `return` anything.


# Under The Hood

Methods are tracked by using `expose` or `expose_as` to create a new class with `MethodSpectator`
descriptors in the place of specified methods. Then, a user will create a `Spectator` using `watch`
which is stored on the instance under the attribute `_instance_spectator`. When a `MethodSpectator`
is accessed through an instance, the descriptor will return a wrapper that will redirect to
`Spectator.wrapper`, which triggers the beforebacks and afterbacks registered to the instance.


# The Bleeding Edge

The following user facing features are only available on `master`, **untested** and subject to frequent **breaking** changes!


## An MVC Framework


If you're using Python 3.6 or greater, `spectate` provides an experimental
Model-View-Controller (MVC) framework within the `spectate.mvc` package. Out of the box
`spectate.mvc` provides three basic model types for `list`, `dict`, and `set`
(Python's three built-in types that are mutable):


```python
from spectate import mvc


d = mvc.Dict()
l = mvc.List()
s = mvc.Set()


@mvc.view(d)
@mvc.view(l)
@mvc.view(s)
def printer(event):
    print(event)


d['a'] = 1
l.append(2)
s.add(3)
```

```
{'key': 'a', 'old': Undefined, 'new': 1}
{'index': 0, 'old': Undefined, 'new': 2}
{'new': {3}, 'old': set()}
```


For most users these built-in types should be enough, however if you're adventurous, then you can define your own `mvc.Model` types.

Let's reconsider the simple `Counter` example from above, and see how we might reimplement that use case with `spectate.mvc`. To begin we must first create a class which inherits from `mvc.Model` - a base class where we can define `mvc.control` methods. These controls ultimately notify views which are hooked into the model:


```python
from spectate import mvc


class Counter(mvc.Model):

    def __init__(self):
        self.x = 0

    def increment(self, amount):
        self.x += amount

    def decrement(self, amount):
        self.x -= amount

    # define a control for incrementing and decrementing
    _control_change = mvc.Control('increment', 'decrement')

    # register a beforeback to the control
    @_control_change.before
    def _control_change(self, call, notify):
        return self.x

    # register an afterback to the control
    @_control_change.after
    def _control_change(self, answer, notify):
        # Send an "event" dictionary to the Counter's views.
        notify(old=answer.before, new=self.x)
```


Once we've defined our `Model` and its `control` methods, we can then use `mvc.view` as we saw above with `List`, `Dict`, and `Set`:


```python
counter = Counter()


@mvc.view(counter)
def printer(event):
    print(event)


counter.increment(1)
counter.decrement(2)
counter.increment(3)
counter.decrement(4)
```

```
{'old': 0, 'new': 1}
{'old': 1, 'new': -1}
{'old': -1, 'new': 2}
{'old': 2, 'new': -2}
```

# Spectate
Create classes whose instances have tracked methods

## Instalation
`spectate` can be installed from GitHub using `pip`:

```
$ pip install git+https://github.com/rmorshea/spectate.git#egg=spectate
```

## Basic Usage
`spectate` is useful for remotely tracking when an instance is modified. This means that protocols
that keep everything up to date and in sync, aren't the outward responsibility of a user, and can
instead be done automagically in the background.

For instance if it were desirable to keep track of element changes in a list. `spectate` could be
used to track `list.__setitiem__` in order to be notified when a user sets the value of an element
in the list. To do this we would first create a `ListSpectator` that inherits from `Spectator`:

```python
from spectate import Spectator

class ListSpectator(Spectator):
    
    def __init__(self, inst):
        super(ListSpectator, self).__init__(inst)
        self._change = {'old': None, 'new': None}
    
    def instance_will_call(self, name, args, kwargs):
        # we know the name will be __setitem__
        # since that's all we're spectating
        index, new = args
        try:
            old = self.inst[index]
        except:
            pass
        else:
            if old != new:
                self._change['old'] = {index: old}
                self._change['new'] = {index: new}
    
    def instance_post_call(self, name, returned):
        o, n = self._change['old'], self._change['new']
        if o and n:
            print("%s : %r -> %r" % (name, o, n))
            self._change['old'] = None
            self._change['new'] = None
```

`instance_will_call` considers the argments being passed to `__setitem__` and determines whether
the value of the element being set will be different. If it's different the new, and old values,
are cached. Then, `instance_post_call` checks to see if a value has changed and prints it.

To implement `ListSpectator`, all we need to do is create a `WatchedList` class using `WatchedType`:

```python
WatchedList = WatchedType('WatchedList', list, ListSpectator, '__setitem__')
```

The instances of `WatchedList` will behave exactly like a `list` in every way. The only difference
being that when a user decides to change the value of a preexisting element, the spectator is notified,
and will print once the action is complete:

```python
l = WatchedList([1, 2, 3])
l[0] = 0
```
```
__setitem__ : {0: 1} -> {0: 2}
```

## Under The Hood
Methods are tracked by creating a new class with `method_spectator` descriptors in the place of
specified methods. At the time an instance of this class is created, a spectator is assigned to
it under the attribute name `instance_spectator`. When a `method_spectator` through an instance,
the descriptor will return a new wrapper function that notifies the `instance_spectator` when the
wrapper is called.

Before the wrapper function returned by a `method_spectator` calls the base method, notifications
are sent to the instance's spectator with the name of the method, and the arguments being passed
to it. Then once the base method is called, a notification is sent to the instance's spectator with
the name of the method, along with the base method's result instead of the arguments.

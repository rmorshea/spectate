[![Build Status](https://travis-ci.org/rmorshea/spectate.svg)](https://travis-ci.org/rmorshea/spectate)


# Spectate


Create classes whose instances have tracked methods


## Installation


+ stable : `pip install spectate`
+ master : `pip install git+https://github.com/rmorshea/spectate.git#egg=spectate`
+ developer : `git clone https://github.com/rmorshea/spectate; cd spectate/; pip install -e .`

## Basic Usage


`spectate` is useful for remotely tracking how an instance is modified. This means that protocols
for managing updates, don't need to be the outward responsibility of a user, and can instead be
done automagically in the background.

For example, if it were desirable to keep track of element changes in a list, `spectate` could be
used to observe `list.__setitiem__` in order to be notified when a user sets the value of an element
in the list. To do this, we would first create an `elist` type using `expose_as`, construct an
instance of that type, and then store callback pairs to that instance's spectator. To access a spectator,
register one with `watch` (e.g. `spectator = watch(the_elist)`), retrieve a preexisting one with the
`watcher` function. Callback pairs are stored by calling the `watcher(the_list).callback` method. You
can then specify, with keywords, whether the callback should be triggered `before`, and/or or `after`
a given method is called - hereafter refered to as "beforebacks" and "afterbacks" respectively.


### Beforebacks


+ Have a signature of `(instance, call)`
    + `instance` is the owner of the method
    + `call` is a `Bunch` with the keys
        + `'name'` - the name of the method which was called
        + `'args'` - the arguments which that method will call
        + `'kwargs'` - the keywords which that method will call
+ Can `return` a value which gets passed on to its respective afterback.


### Afterbacks


+ Have a signature of `(instance, answer)`
    + `instance` is the owner of the method
    + `answer` is a `Bunch` with the keys
        + `'name'` - the name of the method which was called
        + `'value'` - the value returned by the method
        + `'before'` - the value returned by the respective beforeback


## Example


```python
    from spectate import expose_as

    elist = expose_as('elist', list, '__setitem__')

    def pass_on_old_value(inst, call):
        """The beforeback"""
        index = call.args[0]
        old = inst[index]
        return index, old

    def print_element_change(inst, answer):
        """The afterback"""
        # answer.before = pass_on_old_value(call)
        index, old = answer.before
        new = inst[index]
        if new != old:
            print("{%s: %s} -> {%s: %s}" %
                (index, old, index, new))
```

`pass_on_old_value` simply pulls the old value stored at the given index, and then passes
that value and the index on to its afterback. The afterback then checks to see if the value
which is `now` stored at that index, is equal to the value which `was` stored there. If it is,
nothing happens, however if it isn't, the change gets printed.

Instances of `EventfulList` will behave exactly like a `list` in every way. The only
difference being that when a user decides to change the value of a preexisting element, the
spectator is notified, and will print once the action is complete:

```python
    # if a WatchableType is passed to watch, any following
    # arguments are passed to it constructor. Thus a new
    # instance is returned along with its spectator
    l = elist([1, 2, 3]]
    spectator = watch(l)

    spectator.callback('__setitem__',
        before=pass_on_old_value,
        after=print_element_change)

    l[0] = 0
```

Prints `{0: 1} -> {0: 0}`

**[...more examples](https://github.com/rmorshea/spectate/tree/master/examples)**


# Under The Hood


Methods are tracked by using `expose` or (`expose_as`) to create a new class with `MethodSpectator`
descriptors in the place of specified methods. Then, a user will create a `Spectator` using `watch`
which is stored on the instance under the attribute `_instance_spectator`. When a `MethodSpectator`
is accessed through an instance, the descriptor will return a wrapper that will redirect to
`Spectator.wrapper`, which triggers the beforebacks and afterbacks registered to the instance.

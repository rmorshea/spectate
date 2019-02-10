# See End Of File For Licensing

import inspect
import itertools

from .utils import Sentinel
from .base import Model, Control


__all__ = ["List", "Dict", "Set", "Object", "Undefined"]


Undefined = Sentinel("Undefined")


class List(Model, list):
    """A :mod:`spectate.mvc` enabled ``list``."""

    _control_setitem = (
        Control("__setitem__")
        .before("_control_before_setitem")
        .after("_control_after_setitem")
    )
    _control_delitem = (
        Control("__delitem__")
        .before("_control_before_delitem")
        .after("_control_after_delitem")
    )
    _control_insert = (
        Control("insert")
        .before("_control_before_insert")
        .after("_control_after_insert")
    )
    _control_append = Control("append").after("_control_after_append")
    _control_extend = (
        Control("extend")
        .before("_control_before_extend")
        .after("_control_after_extend")
    )
    _control_pop = (
        Control("pop").before("_control_before_pop").after("_control_after_delitem")
    )
    _control_clear = (
        Control("clear").before("_control_before_clear").after("_control_after_clear")
    )
    _control_remove = (
        Control("remove")
        .before("_control_before_remove")
        .after("_control_after_delitem")
    )
    _control_rearrangement = (
        Control("sort", "reverse")
        .before("_control_before_rearrangement")
        .after("_control_after_rearrangement")
    )

    def _control_before_setitem(self, call, notify):
        index = call.args[0]
        try:
            old = self[index]
        except KeyError:
            old = Undefined
        return index, old

    def _control_after_setitem(self, answer, notify):
        index, old = answer.before
        new = self[index]
        if new is not old:
            notify(index=index, old=old, new=new)

    def _control_before_delitem(self, call, notify):
        index = call.args[0]
        return index, self[index:]

    def _control_after_delitem(self, answer, notify):
        index, old = answer.before
        for i, x in enumerate(old):
            try:
                new = self[index + i]
            except IndexError:
                new = Undefined
            notify(index=(i + index), old=x, new=new)

    def _control_before_insert(self, call, notify):
        index = call.args[0]
        return index, self[index:]

    def _control_after_insert(self, answer, notify):
        index, old = answer.before
        for i in range(index, len(self)):
            try:
                o = old[i]
            except IndexError:
                o = Undefined
            notify(index=i, old=o, new=self[i])

    def _control_after_append(self, answer, notify):
        notify(index=len(self) - 1, old=Undefined, new=self[-1])

    def _control_before_extend(self, call, notify):
        return len(self)

    def _control_after_extend(self, answer, notify):
        for i in range(answer.before, len(self)):
            notify(index=i, old=Undefined, new=self[i])

    def _control_before_pop(self, call, notify):
        if not call.args:
            index = len(self) - 1
        else:
            index = call.args[0]
        return index, self[index:]

    def _control_before_clear(self, call, notify):
        return self.copy()

    def _control_after_clear(self, answer, notify):
        for i, v in enumerate(answer.before):
            notify(index=i, old=v, new=Undefined)

    def _control_before_remove(self, call, notify):
        index = self.index(call.args[0])
        return index, self[index:]

    def _control_before_rearrangement(self, call, notify):
        return self.copy()

    def _control_after_rearrangement(self, answer, notify):
        old = answer.before
        for i, v in enumerate(old):
            if v != self[i]:
                notify(index=i, old=v, new=self[i])


class Dict(Model, dict):
    """A :mod:`spectate.mvc` enabled ``dict``."""

    _control_setitem = (
        Control("__setitem__", "setdefault")
        .before("_control_before_setitem")
        .after("_control_after_setitem")
    )

    _control_delitem = (
        Control("__delitem__", "pop")
        .before("_control_before_delitem")
        .after("_control_after_delitem")
    )

    _control_update = (
        Control("update")
        .before("_control_before_update")
        .after("_control_after_update")
    )

    _control_clear = (
        Control("clear").before("_control_before_clear").after("_control_after_clear")
    )

    def _control_before_setitem(self, call, notify):
        key = call.args[0]
        old = self.get(key, Undefined)
        return key, old

    def _control_after_setitem(self, answer, notify):
        key, old = answer.before
        new = self[key]
        if new != old:
            notify(key=key, old=old, new=new)

    def _control_before_delitem(self, call, notify):
        key = call.args[0]
        try:
            return key, self[key]
        except KeyError:
            # the base method will error on its own
            pass

    def _control_after_delitem(self, answer, notify):
        key, old = answer.before
        notify(key=key, old=old, new=Undefined)

    def _control_before_update(self, call, notify):
        if len(call.args):
            args = call.args[0]
            if inspect.isgenerator(args):
                # copy generator so it doesn't get exhausted
                args = itertools.tee(args)[1]
            new = dict(args)
            new.update(call.kwargs)
        else:
            new = call.kwargs
        old = {k: self.get(k, Undefined) for k in new}
        return old

    def _control_after_update(self, answer, notify):
        for k, v in answer.before.items():
            if self[k] != v:
                print(k, v)
                notify(key=k, old=v, new=self[k])

    def _control_before_clear(self, call, notify):
        return self.copy()

    def _control_after_clear(self, answer, notify):
        for k, v in answer.before.items():
            notify(key=k, old=v, new=Undefined)


class Set(Model, set):
    """A :mod:`spectate.mvc` enabled ``set``."""

    _control_update = Control(
        "clear",
        "update",
        "difference_update",
        "intersection_update",
        "add",
        "pop",
        "remove",
        "symmetric_difference_update",
        "discard",
    )

    @_control_update.before
    def _control_update(self, call, notify):
        return self.copy()

    @_control_update.after
    def _control_update(self, answer, notify):
        new = self.difference(answer.before)
        old = answer.before.difference(self)
        if new or old:
            notify(new=new, old=old)


class Object(Model):
    """A :mod:`spectat.mvc` enabled ``object``."""

    _control_attr_change = Control("__setattr__", "__delattr__")

    def __init__(self, *args, **kwargs):
        self.__dict__.update(*args, **kwargs)

    @_control_attr_change.before
    def _control_attr_change(self, call, notify):
        return call.args[0], getattr(self, call.args[0], Undefined)

    @_control_attr_change.after
    def _control_attr_change(self, answer, notify):
        attr, old = answer.before
        new = getattr(self, attr, Undefined)
        if new != old:
            notify(attr=attr, old=old, new=new)


# The MIT License (MIT)

# Copyright (c) 2016 Ryan S. Morshead

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

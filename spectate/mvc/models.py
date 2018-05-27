# See End Of File For Licensing

from .utils import Sentinel
from .base import Model, control


__all__ = [
    'List',
    'Dict',
    'Set',
    'Undefined',
]


Undefined = Sentinel('Undefined')


class List(Model, list):
    """An MVC enabled ``list``."""

    @control.before('__setitem__')
    def _control_setitem(self, call, notify):
        index = call.args[0]
        try:
            old = self[index]
        except KeyError:
            old = Undefined
        return index, old

    @_control_setitem.after
    def _control_setitem(self, answer, notify):
        index, old = answer.before
        new = self[index]
        if new is not old:
            notify(index=index, old=old, new=new)

    @control.before('__delitem__')
    def _control_delitem(self, call, notify):
        index = call.args[0]
        return index, self[index:]

    @_control_delitem.after
    def _control_delitem(self, answer, notify):
        index, old = answer.before
        for i, x in enumerate(old):
            try:
                new = self[index + i]
            except IndexError:
                new = Undefined
            notify(index=(i + index), old=x, new=new)

    @control.before('insert')
    def _control_insert(self, call, notify):
        index = call.args[0]
        return index, self[index:]

    @_control_insert.after
    def _control_insert(self, answer, notify):
        index, old = answer.before
        for i in range(index, len(self)):
            try:
                o = old[i]
            except IndexError:
                o = Undefined
            notify(index=i, old=o, new=self[i])

    @control.after('append')
    def _control_append(self, answer, notify):
        notify(index=len(self) - 1, old=Undefined, new=self[-1])

    @control.before('extend')
    def _control_extend(self, call, notify):
        return len(self)

    @_control_extend.after
    def _control_extend(self, answer, notify):
        for i in range(answer.before, len(self)):
            notify(index=i, old=Undefined, new=self[i])

    @control.after('pop')
    def _control_pop(self, answer, notify):
        notify(index=len(self), old=answer.value, new=Undefined)

    @control.before('remove')
    def _control_remove(self, call, notify):
        index = self.index(call.args[0])
        return index, self[index:]

    _control_remove.after(_control_delitem)

    @control.before('reverse')
    def _before_reverse(self, call, notify):
        return self._control_rearrangement(self)

    @control.before('sort')
    def _before_sort(self, call, notify):
        return self._control_rearrangement(self)

    @staticmethod
    def _control_rearrangement(new):
        old = new[:]
        def _after_rearangement(returned, notify):
            for i, v in enumerate(old):
                if v != new[i]:
                    notify(index=i, old=v, new=new[i])
        return _after_rearangement


class Dict(Model, dict):
    """An MVC enabled ``dict``."""

    _model_selector_template = '{key}'

    @control.before('__setitem__', 'setdefault')
    def _control_setitem(self, call, notify):
        key = call.args[0]
        old = self.get(key, Undefined)
        return key, old

    @_control_setitem.after
    def _control_setitem(self, answer, notify):
        key, old = answer.before
        new = self[key]
        if new != old:
            notify(key=key, old=old, new=new)

    @control.before('__delitem__', 'pop')
    def _control_delitem(self, call, notify):
        key = call.args[0]
        try:
            old = self[key]
        except KeyError:
            pass
        else:
            def _after(returned):
                notify(key=key, old=old, new=Undefined)
            return _after

    @control.before('update')
    def _control_update(self, call, notify):
        if len(call.args):
            args = call.args[0]
            if inspect.isgenerator(arg):
                # copy generator so it doesn't get exhausted
                arg = itertools.tee(arg)[1]
            new = dict(arg)
            new.update(call.kwargs)
        else:
            new = call.kwargs
        old = {k: self.get(k, Undefined) for k in new}
        return old

    @_control_update.after
    def _control_update(self, answer, notify):
        for k, v in answer.before.items():
            if self[k] != v:
                notify(key=k, old=v, new=self[k])

    @control.before('clear')
    def _control_clear(self, call, notify):
        return self.copy()

    @_control_clear.after
    def _control_clear(self, answer, notify):
        for k, v in answer.before.items():
            notify(key=k, old=v, new=Undefined)


class Set(Model, set):
    """An MVC enabled ``set``."""

    @control.before(
        "clear", "update", "difference_update", "intersection_update",
        "add", "pop", "remove", "symmetric_difference_update", "discard")
    def _control_update(self, call, notify):
        return self.copy()

    @_control_update.after
    def _control_update(self, answer, notify):
        new = self.difference(answer.before)
        old = answer.before.difference(self)
        if new or old:
            notify(new=new, old=old)


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

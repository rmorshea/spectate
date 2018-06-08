# See End Of File For Licensing

from contextlib import contextmanager
from functools import wraps, partial
from collections import defaultdict

from .utils import memory_safe_function, Sentinel
from ..spectate import Watchable, Data, MethodSpectator, expose, watched

__all__ = [
    'Model',
    'Control',
    'view',
    'unview',
    'is_model',
    'hold',
    'mute',
]


def is_model(model, raises=False):
    if isinstance(model, Model):
        return True
    elif raises:
        raise TypeError('Expected a Model, not %r.' % model)
    else:
        return False


@contextmanager
def hold(model):
    is_model(model, raises=True)
    events = []
    redirect = lambda e : events.extend(e)
    restore = model.__dict__.get('_notify_model_views')
    model._notify_model_views = redirect

    try:
        yield events
    finally:
        if restore is None:
            del model._notify_model_views
        else:
            model._notify_model_views = restore
        model._notify_model_views(tuple(events))


@contextmanager
def mute(model):
    is_model(model, raises=True)
    redirect = lambda e : None
    restore = model.__dict__.get('_notify_model_views')
    model._notify_model_views = redirect
    try:
        yield
    finally:
        if restore is None:
            del model._notify_model_views
        else:
            model._notify_model_views = restore


def views(model):
    """Return a model's views keyed on what events they respond to."""
    is_model(model, raises=True)
    return model._model_views[:]


def view(model):
    is_model(model, raises=True)
    def setup(function):
        # we want to avoid circular references.
        safe = memory_safe_function(function)
        model._model_views.append(safe)
        return safe
    return setup


def unview(model, function):
    model._model_views.remove(function)


class Control:

    def __init__(self, *methods):
        self.methods = methods
        self.name = None

    def before(self, callback):
        if isinstance(callback, Control):
            callback = callback._before
        elif not isinstance(callback, str):
            callback = self._wrap(callback)
        self._before = callback
        return self

    def after(self, callback):
        if isinstance(callback, Control):
            callback = callback._after
        elif not isinstance(callback, str):
            callback = self._wrap(callback)
        self._after = callback
        return self

    @staticmethod
    def _wrap(function):
        if function is None:
            return None
        @wraps(function)
        def callback(self, *args, **kwargs):
            events = []
            def notify(**event):
                events.append(Data(event))
            args = args + (notify,)
            result = function(self, *args, **kwargs)
            if events:
                self._notify_model_views(tuple(events))
            return result
        return callback

    _after, _before = None, None

    def __set_name__(self, cls, name):
        if not issubclass(cls, Model):
            raise TypeError("Can only define a control on a Model, not %r" % cls)
        if self.name:
            msg = 'Control was defined twice - %r and %r.'
            raise RuntimeError(msg % (self.name, name))
        else:
            self.name = name
        if isinstance(self._after, str):
            self._after = self._wrap(getattr(cls, self._after))
        if isinstance(self._before, str):
            self._before = self._wrap(getattr(cls, self._before))
        for m in self.methods:
            setattr(cls, m, MethodSpectator(getattr(cls, m), m))


class Model(Watchable):

    _model_controls = ()

    def __init_subclass__(cls, **kwargs):
        for k, v in list(cls.__dict__.items()):
            if isinstance(v, Control):
                cls._model_controls += (k,)
        super().__init_subclass__(**kwargs)

    def __new__(cls, *args, **kwargs):
        self, spectator = watched(super().__new__, cls)
        for name in cls._model_controls:
            ctrl = getattr(cls, name)
            for method in ctrl.methods:
                before, after = ctrl._before, ctrl._after
                spectator.callback(method, before, after)
        self._model_views = []
        self.__init__(*args, **kwargs)
        return self

    def _notify_model_views(self, events):
        for view in self._model_views:
            view(events)


_Empty = Sentinel('Empty')

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

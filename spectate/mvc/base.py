# See End Of File For Licensing

from contextlib import contextmanager
from functools import wraps
from collections import defaultdict

from .utils import memory_safe_function
from ..spectate import Watchable, Data, MethodSpectator, expose, watched

__all__ = [
    'Model',
    'Control',
    'view',
    'unview',
    'hold',
    'mute',
]


@contextmanager
def hold(model):
    if not isinstance(model, Model):
        raise TypeError('Expected a Model, not %r.' % model)
    events = []
    redirect = lambda e : events.append(e)
    restore = model.__dict__.get('_notify_model_views')
    model._notify_model_views = redirect

    try:
        yield events
    finally:
        if restore is None:
            del model._notify_model_views
        else:
            model._notify_model_views = restore
        for e in events:
            model._notify_model_views(e)


@contextmanager
def mute(model):
    if not isinstance(model, Model):
        raise TypeError('Expected a Model, not %r.' % model)
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
    if not isinstance(model, Model):
        raise TypeError('%r is not a Model.' % model)
    return {s : l[:] for s, l in model._model_views.items()}


def view(*models, **select):
    def setup(function):
        # we want to avoid circular references.
        safe = memory_safe_function(function)
        for model in models:
            if not isinstance(model, Model):
                raise TypeError('%r is not a Model.' % model)
            if not select:
                model._model_views[None].append(safe)
            else:
                selector = model._model_event_selector.format(**select)
                model._model_views[selector].append(safe)
        return safe
    return setup


def unview(*models, **select):
    def setup(function):
        for model in models:
            if not isinstance(model, Model):
                raise TypeError('%r is not a Model.' % model)
            if select:
                selector = model._model_event_selector.format(**select)
            else:
                selector = None
            model._model_views[selector].remove(function)


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
            def notify(*args, **kwargs):
                event = Data(*args, **kwargs)
                self._notify_model_views(event)
            return function(self, *(args + (notify,)), **kwargs)
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
    _model_event_selector = ''

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
        self._model_views = defaultdict(list)
        self.__init__(*args, **kwargs)
        return self

    def _notify_model_views(self, event):
        selector = self._model_event_selector.format(**event)
        for view in self._model_views[selector]:
            view(event)
        for view in self._model_views[None]:
            view(event)


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

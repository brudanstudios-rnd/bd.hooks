__all__ = ["HookRegistry"]

import weakref
import types
import logging

from .exceptions import \
    InvalidCallbackError, \
    HookNotFoundError, \
    HookCallbackDeadError, \
    CallbackExecutionError

LOGGER = logging.getLogger(__name__)


class HookItem(object):

    def __init__(self, name, callback, priority=50):
        self._name = name
        self._obj_weakref = None
        self._callback = callback
        self._priority = priority

        if isinstance(callback, types.MethodType):
            self._callback = callback.im_func
            self._obj_weakref = weakref.ref(callback.im_self)

    @property
    def priority(self):
        return self._priority

    def execute(self, *args, **kwargs):
        try:
            if self._obj_weakref is None:  # is a function
                return self._callback(*args, **kwargs)
            else:
                return self._callback(self._obj_weakref(), *args, **kwargs)
        except Exception as e:
            raise CallbackExecutionError(details={"hook_name": self._name,
                                                  "callback": str(self._callback),
                                                  "exc_msg": str(e)})

    def is_valid(self):
        if self._obj_weakref is not None and self._obj_weakref() is None:
            return False

        if self._callback is None:
            return False

        return True


class HookRegistry(object):

    def __init__(self):
        self._hooks = {}
        self._sorted = set()

    def add_hook(self, name, callback, priority=50):
        if not callable(callback):
            raise InvalidCallbackError(details={"hook_name": name,
                                                "callback": str(callback)})

        LOGGER.debug("Adding hook: {} ...".format(name))

        hooks = self._hooks.get(name, [])

        hooks.append(HookItem(name, callback, priority))

        self._hooks[name] = hooks

        LOGGER.debug("Done")

    def get_hooks(self, name):
        hooks = self._hooks.get(name)

        if not hooks:
            raise HookNotFoundError(details={"hook_name": name})

        self._cleanup(name)

        if name not in self._sorted:
            hooks.sort(key=lambda h: h.priority, reverse=True)
            self._sorted.add(name)

        return hooks

    def _cleanup(self, name):
        hooks = self._hooks.get(name)

        # remove all the method callbacks bound to the deleted objects
        for i in range(len(hooks)-1, -1, -1):

            # chech if it is a method and the owner is dead
            if not hooks[i].is_valid():
                del hooks[i]

        # remove this hook from the registry
        # if there is no callbacks left
        if not hooks:
            del self._hooks[name]
            if name in self._sorted:
                self._sorted.remove(name)
            raise HookCallbackDeadError(details={"hook_name": name})
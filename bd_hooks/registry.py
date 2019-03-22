__all__ = ["HookRegistry"]

import weakref
import types
import logging

import six

from .exceptions import \
    InvalidCallbackError, \
    HookNotFoundError, \
    HookCallbackDeadError, \
    CallbackExecutionError

LOGGER = logging.getLogger(__name__)


class HookItem(object):

    def __init__(self, name, callback, priority=50):
        self._name = name
        self._callback = callback
        self._priority = priority

    @property
    def priority(self):
        return self._priority

    def execute(self, *args, **kwargs):
        """Execute callback with the provided arguments.


        """
        raise NotImplementedError()

    def is_valid(self):
        """Test whether the hook item is valid.

        Returns:
            bool: True if valid, False otherwise.

        """
        raise NotImplementedError()

    @classmethod
    def create(cls, name, callback, priority=50):
        """
        Factory method to initialize a HookItem subclass suitable
        for a provided callback type.

        Args:
            name (str): A hook name.
            callback (callable): Function or method.
            priority (int): Priority level.
                Execution starts from the items with the highest
                priority and follows to the items with the lower one.
                If multiple items have exactly the same priority, they
                will be executed in the order they were added into the
                registry.

        """
        item_class = HookFunctionItem
        if isinstance(callback, types.MethodType):
            item_class = HookMethodItem
        return item_class(name, callback, priority)


class HookFunctionItem(HookItem):

    def execute(self, *args, **kwargs):
        try:
            return self._callback(*args, **kwargs)
        except Exception as e:
            raise CallbackExecutionError(details={"hook_name": self._name,
                                                  "callback": str(self._callback),
                                                  "exc_msg": str(e)})

    def is_valid(self):
        return self._callback is not None


class HookMethodItem(HookItem):

    def __init__(self, name, callback, priority=50):
        super(HookMethodItem, self).__init__(name, callback, priority)
        self._callback = six.get_method_function(callback)
        self._obj_weakref = weakref.ref(six.get_method_self(callback))

    def is_valid(self):
        return self._obj_weakref is not None and \
               self._obj_weakref() is not None

    def execute(self, *args, **kwargs):
        try:
            return self._callback(self._obj_weakref(), *args, **kwargs)
        except Exception as e:
            raise CallbackExecutionError(details={"hook_name": self._name,
                                                  "callback": str(self._callback),
                                                  "exc_msg": str(e)})


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

        hooks.append(HookItem.create(name, callback, priority))

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
__all__ = ["HookRegistry"]

import logging

from .exceptions import \
    InvalidCallbackError, \
    HookNotFoundError, \
    HookCallbackDeadError, \
    CallbackExecutionError

LOGGER = logging.getLogger(__name__)


class HookItem(object):

    def __init__(self, name, callback, priority=50):
        """Constructor.

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
        self._name = name
        self._callback = callback
        self._priority = priority

    @property
    def priority(self):
        return self._priority

    def execute(self, *args, **kwargs):
        """Execute callback with any provided arguments."""
        try:
            return self._callback(*args, **kwargs)
        except Exception as e:
            raise CallbackExecutionError(details={"hook_name": self._name,
                                                  "callback": str(self._callback),
                                                  "exc_msg": str(e)})


class HookRegistry(object):

    def __init__(self):
        self._data = {}
        self._sorted = set()

    def add_hook(self, name, callback, priority=50):
        if not callable(callback):
            raise InvalidCallbackError(details={"hook_name": name,
                                                "callback": str(callback)})

        LOGGER.debug("Adding hook: {} ...".format(name))

        hooks = self._data.get(name, [])

        hooks.append(HookItem(name, callback, priority))

        self._data[name] = hooks

        LOGGER.debug("Done")

    def get_hooks(self, name):
        hooks = self._data.get(name)
        if not hooks:
            raise HookNotFoundError(details={"hook_name": name})

        if name not in self._sorted:
            hooks.sort(key=lambda h: h.priority, reverse=True)
            self._sorted.add(name)

        return hooks

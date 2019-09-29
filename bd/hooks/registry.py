__all__ = ["HookRegistry"]

import logging

from .exceptions import \
    InvalidCallbackError, \
    HookNotFoundError, \
    CallbackExecutionError

LOGGER = logging.getLogger(__name__)


class HookItem(object):
    """This class stores and executes an individual callback function."""

    def __init__(self, hook_name, callback, priority=50):
        """Constructor.

        Args:
            hook_name (str): A hook name.
            callback (callable): Function or method.
            priority (int): Priority level.
                Execution starts from the items with the highest
                priority and follows to the items with the lower one.
                If multiple items have exactly the same priority, they
                will be executed in the order they were added into the
                registry.
        """
        self._hook_name = hook_name
        self._callback = callback
        self._priority = priority

    @property
    def priority(self):
        return self._priority

    def execute(self, *args, **kwargs):
        """Execute callback with any provided arguments.

        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        Returns:
            Return value from the executed callback.

        Raises:
            CallbackExecutionError: Raised on any error
                during callback execution.

        """
        try:
            return self._callback(*args, **kwargs)
        except Exception as e:
            raise CallbackExecutionError(details={"hook_name": self._hook_name,
                                                  "callback": str(self._callback),
                                                  "exc_msg": str(e)})


class HookRegistry(object):
    """This class is used to add and retrieve hook items.

    It is passed as an argument into the 'register' function
    of every individual plugin to allow it to decide which
    callback is going to be registered for which hook name.

    """
    def __init__(self):

        # maps hook name to all the registered hook items for that name
        self._data = {}

        # a set of hook names for which the hook items were already sorted by priority
        self._sorted = set()

    def add_hook(self, name, callback, priority=50):
        """Associated a callback with the hook name.

        Args:
            name: A hook name.
            callback (callable): Function or method.
            priority (int): Priority level.
                Execution starts from the items with the highest
                priority and follows to the items with the lower one.
                If multiple items have exactly the same priority, they
                will be executed in the order they were added into the
                registry.
        Raises:
            InvalidCallbackError: If the 'callback' argument is not callable.

        """
        if not callable(callback):
            raise InvalidCallbackError(details={"hook_name": name,
                                                "callback": str(callback)})

        LOGGER.debug("Adding hook: {} ...".format(name))

        hooks = self._data.get(name, [])

        hooks.append(HookItem(name, callback, priority))

        self._data[name] = hooks

        LOGGER.debug("Done")

    def get_hooks(self, name):
        """Return a list of hook items registered under the specified hook name.

        It also sorts hook items by their priorities in the descending order,
        so the item with the highest priority goes first.

        Args:
            name: A hook name.

        Returns:
            list[HookItem]: A list of all the hook items
                registered under the specified hook name.

        Raises:
            HookNotFoundError: If the hook name has no registered hook items.

        """
        hooks = self._data.get(name)
        if not hooks:
            raise HookNotFoundError(details={"hook_name": name})

        if name not in self._sorted:
            hooks.sort(key=lambda h: h.priority, reverse=True)
            self._sorted.add(name)

        return hooks

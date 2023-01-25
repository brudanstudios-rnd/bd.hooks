__all__ = ["HookRegistry"]

import sys
import uuid
import logging
import inspect

from .exceptions import InvalidCallbackError, HookNotFoundError, CallbackExecutionError

logger = logging.getLogger(__name__)


class HookItem(object):
    """This class stores and executes an individual callback function."""

    def __init__(self, uid, callback, filename, priority=50):
        """Constructor.

        Args:
            uid: A hook uid.
            callback (callable): Function or method.
            filename (str): A path to the file where the callback resides.
            priority (int): Priority level.
                Execution starts from the items with the highest
                priority and follows to the items with the lower one.
                If multiple items have exactly the same priority, they
                will be executed in the order they were added into the
                registry.
        """
        self._uid = uid
        self._callback = callback
        self._filename = filename
        self._priority = priority

    @property
    def priority(self):
        return self._priority

    @property
    def filename(self):
        return self._filename

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
        except CallbackExecutionError as e:
            raise
        except Exception as e:
            _type, _, traceback = sys.exc_info()
            raise CallbackExecutionError(
                f"({_type.__name__}) {str(e)}",
                details={
                    "hook_item": self,
                    "source_exception": e,
                },
            ).with_traceback(traceback) from None

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return "HookItem('{0}', '{1}::{2}', {3})".format(
            self._uid,
            self._filename,
            self._callback.__name__,
            self._priority,
        )


class HookRegistry(object):
    """This class is used to add and retrieve hook items.

    It is passed as an argument into the 'register' function
    of every individual plugin to allow it to decide which
    callback is going to be registered for which hook uid.

    """

    def __init__(self):

        # maps hook uid to all the registered hook items for that uid
        self._data = {}

        # a set of hook names for which the hook items were already sorted by priority
        self._sorted = set()

    def add_hook(self, uid, callback, priority=50):
        """Associated a callback with the hook uid.

        Args:
            uid: A hook identifier.
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
        filename = inspect.stack()[1].filename

        if not callable(callback):
            raise InvalidCallbackError(
                details={
                    "hook_uid": uid,
                    "module_path": filename,
                    "callback": str(callback),
                }
            )

        logger.debug("Registering item for '{}' hook...".format(uid))

        if inspect.isclass(callback):
            callback.__name__ = "{0}__{1}".format(callback.__name__, uuid.uuid4().hex)

        hooks = self._data.get(uid, [])

        hook_item = HookItem(uid, callback, filename, priority)

        hooks.append(hook_item)

        self._data[uid] = hooks

        logger.debug("Registered {}".format(str(hook_item)))

    def get_hooks(self, uid):
        """Return a list of hook items registered under the specified hook uid.

        It also sorts hook items by their priorities in the descending order,
        so the item with the highest priority goes first.

        Args:
            uid: A hook unique identifier.

        Returns:
            list[HookItem]: A list of all the hook items
                registered under the specified hook uid.

        Raises:
            HookNotFoundError: If the hook uid has no registered hook items.

        """
        hooks = self._data.get(uid)
        if not hooks:
            raise HookNotFoundError(details={"hook_uid": uid})

        if uid not in self._sorted:
            hooks.sort(key=lambda h: h.priority, reverse=True)
            self._sorted.add(uid)

        return hooks

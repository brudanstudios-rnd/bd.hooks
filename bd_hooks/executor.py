import logging

from .exceptions import CallbackExecutionError


LOGGER = logging.getLogger('bd.' + __name__)


class HookExecutor(object):
    """This class allows the user to choose how to execute the hooks."""

    def __init__(self, hook_items, *args, **kwargs):
        """Constructor.

        Args:
            hook_items (list[bd_hooks.registry.HookItem]):
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        """
        self._hook_items = hook_items
        self._args = args
        self._kwargs = kwargs

    def all(self, result_callback=None, safe_execute=False):
        """Executes all the hook callbacks sequentially.

        Args:
            result_callback (callable): A callback to pass
                each hook item execution result into.
            safe_execute (bool):

        Raises:
            CallbackExecutionError: Raised if safe_execute is False and any error
                occurs during the callback execution.

        """
        for hook_item in self._hook_items:
            try:
                result = hook_item.execute(*self._args, **self._kwargs)
            except CallbackExecutionError as e:
                if safe_execute:
                    LOGGER.warning(e)
                else:
                    raise

            else:
                if result_callback:
                    result_callback(result)

    def one(self):
        """Executes only the first hook callback.

        Returns:
            Return value from the executed callback.

        Raises:
            CallbackExecutionError: Raised on any error
                during callback execution.

        """
        return self._hook_items[0].execute(*self._args, **self._kwargs)
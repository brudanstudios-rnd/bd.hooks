import logging
from functools import partial
from typing import Any, Callable, Generator, List, Optional, Union

from .registry import HookItem
from .exceptions import CallbackExecutionError


logger = logging.getLogger(__name__)


class HookExecutionControl:
    def __init__(
        self,
        on_released_callback: Optional[Callable[[], Any]] = None,
        on_interrupted_callback: Optional[Callable[[Optional[str]], Any]] = None,
    ):
        self._on_released_callback = on_released_callback
        self._on_interrupted_callback = on_interrupted_callback
        self._is_released = False
        self._is_interrupted = False

    def interrupt(self, message: Optional[str] = None):
        self._is_interrupted = True
        if callable(self._on_interrupted_callback):
            self._on_interrupted_callback(message)

    def is_interrupted(self):
        return self._is_interrupted

    def release(self):
        if self._is_interrupted or self._is_released:
            return

        if callable(self._on_released_callback):
            self._on_released_callback()

    def __del__(self):
        self.release()


class HookExecutor(object):
    """This class allows user to choose how to execute the hooks."""

    def __init__(self, hook_items: List[HookItem], *args, **kwargs):
        """Constructor.

        Args:
            hook_items: A list of HookItem objects to execute.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.

        """
        self._hook_items = hook_items
        self._args = args
        self._kwargs = kwargs

    def all(
        self,
        result_callback: Optional[Callable[[Any], Any]] = None,
        safe_execute: bool = False,
        on_finished_callback: Optional[Callable[[], Any]] = None,
        on_interrupted_callback: Optional[Callable[[Optional[str]], Any]] = None,
    ):
        """Execute all the hook callbacks sequentially.

        Args:
            result_callback: A callback to execute when the result is ready.
            safe_execute: Log warning instead of throwing the CallbackExecutionError.
            on_finished_callback: A callback to execute when the
                last hook item is executed successfully.
            on_interrupted_callback: A callback to execute when
                the HookItem requested an interruption.
        Raises:
            CallbackExecutionError: Raised if safe_execute is False and any error
                occurs during the callback execution.

        """

        def _chain():
            for hook_item in self._hook_items:
                yield partial(hook_item.execute, *self._args, **self._kwargs)

        chain = _chain()

        def _go_next():
            try:
                callback = next(chain)
            except StopIteration:
                if callable(on_finished_callback):
                    on_finished_callback()
                return

            control = HookExecutionControl(
                on_released_callback=_go_next,
                on_interrupted_callback=on_interrupted_callback,
            )
            try:
                try:
                    result = callback(hook_control=control)
                except CallbackExecutionError as e:
                    if str(e).endswith(
                        "got an unexpected keyword argument 'hook_control'"
                    ):
                        result = callback()
                    else:
                        raise
            except CallbackExecutionError as e:
                if safe_execute:
                    logger.warning(e)
                else:
                    raise

            else:
                if callable(result_callback):
                    result_callback(result)

        _go_next()

    def one(self) -> Any:
        """Execute only the first hook callback.

        Returns:
            Return value from the executed callback.

        Raises:
            CallbackExecutionError: Raised on any error
                during callback execution.

        """
        return self._hook_items[0].execute(*self._args, **self._kwargs)

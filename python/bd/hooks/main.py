__all__ = ["load", "execute", "get_active_registry"]

import os
import sys
import logging

from . import registry, loader, executor
from .exceptions import HooksNotLoadedError

logger = logging.getLogger(__name__)
_registry = None


def load(hook_search_paths=None):
    """Find and load all the available hooks.

    Args:
        hook_search_paths (list[str]): A list of directories
            in which to search plugins.

    """
    if hook_search_paths is None:
        hook_search_paths = []
    else:
        # convert all search paths to strings
        hook_search_paths = list(map(str, hook_search_paths))

    global _registry

    if _registry is None:
        # extract search paths from environment variable
        BD_HOOKPATH = os.getenv("BD_HOOKPATH")
        if BD_HOOKPATH:
            hook_search_paths.extend(BD_HOOKPATH.split(os.pathsep))

        if not hook_search_paths:
            logger.warning(
                "Hook search paths are not provided. "
                "Check if 'BD_HOOKPATH' environment variable exists"
            )
            return

        _registry = registry.HookRegistry()

    if hook_search_paths:
        loader.load(_registry, hook_search_paths)


def execute(hook_uid, *args, **kwargs):
    """
    Get all hook items registered under the specified hook uid
    and prepare a HookExecutor object with the provided arguments.

    Args:
        hook_uid: A hook identifier.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        bd.hooks.executor.HookExecutor: hook executor object.

    """
    if _registry is None:
        raise HooksNotLoadedError(
            "Hook Registry not initialized. Possible cause: 'load' function not called. "
        )

    hook_items = _registry.get_hooks(hook_uid)
    return executor.HookExecutor(hook_items, *args, **kwargs)


def get_active_registry():
    return _registry

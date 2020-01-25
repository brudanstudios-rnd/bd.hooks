__all__ = ["load", "execute"]

import sys

from . import registry, loader, executor

this = sys.modules[__name__]
this._registry = None


def load(hook_search_paths=None):
    """Find and load all the available hooks.

    Args:
        hook_search_paths (list[str]): A list of directories
            in which to search plugins.

    """
    if this._registry is None:
        this._registry = registry.HookRegistry()
        loader.load(this._registry, hook_search_paths)


def execute(hook_name, *args, **kwargs):
    """
    Get all hook items registered under the specified hook name
    and prepare a HookExecutor object with the provided arguments.

    Args:
        hook_name (str): A hook name.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        bd.hooks.executor.HookExecutor: hook executor object.

    """
    hook_items = this._registry.get_hooks(hook_name)
    return executor.HookExecutor(hook_items, *args, **kwargs)

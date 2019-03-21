__all__ = ["load_hooks", "execute"]

import sys

from .registry import *
from .loader import *
from .executor import *

this = sys.modules[__name__]
this._registry = None


def load_hooks(hook_search_paths=None):
    if this._registry is None:
        this._registry = HookRegistry()
        HookLoader.load(this._registry, hook_search_paths)


def execute(hook_name, *args, **kwargs):
    hook_items = this._registry.get_hooks(hook_name)
    return HookExecutor(hook_items, *args, **kwargs)

__all__ = ["load_hooks", "execute"]

import sys

from .registry import *
from .loader import *
from .executor import *

this = sys.modules[__name__]
this._registry = None


def load_hooks(hook_search_paths=None, loader=HookLoader):
    if this._registry is None:
        this._registry = HookRegistry()
        loader.load(this._registry, hook_search_paths)


def execute(hook_name, *args, **kwargs):
    return HookExecutor(this._registry, hook_name, *args, **kwargs)

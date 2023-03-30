__all__ = [
    "HookError",
    "HookNotFoundError",
    "CallbackExecutionError",
    "InvalidCallbackError",
]

from typing import Any, Dict, Optional


class HookError(Exception):
    def __init__(
        self, message: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.details = details or {}


class HooksNotLoadedError(HookError):
    pass


class InvalidCallbackError(HookError):
    pass


class CallbackExecutionError(HookError):
    pass


class HookNotFoundError(HookError):
    pass

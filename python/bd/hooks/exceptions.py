__all__ = [
    "HookError",
    "HookNotFoundError",
    "CallbackExecutionError",
    "InvalidCallbackError",
]

from typing import Any, Dict, Optional


class HookError(Exception):

    default_message = "Unspecified error occurred"

    def __init__(
        self, message: Optional[str] = None, details: Optional[Dict[str, Any]] = None
    ):
        self.message = message or self.default_message
        self.details = details or {}

    def __str__(self):
        return str(self.message.format(**self.details))


class HooksNotLoadedError(HookError):
    default_message = (
        "Hook Registry not initialized. Possible cause: 'load' function not called. "
    )


class InvalidCallbackError(HookError):
    default_message = (
        "Invalid callback '{module_path}:{callback}' provided for '{hook_uid}' hook"
    )


class CallbackExecutionError(HookError):
    default_message = "Failed to execute '{hook_item}'. {source_exception}"


class HookNotFoundError(HookError):
    default_message = "Unable to find a hook '{hook_uid}'"

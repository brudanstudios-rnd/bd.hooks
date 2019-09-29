import sys
import traceback

import six


class Error(Exception):

    default_message = "Unspecified error occurred"

    def __init__(self, message=None, details=None):
        self.message = message or self.default_message
        self.details = details or {}
        self.traceback = traceback.format_exc()

    def __str__(self):
        details = {}
        for key, value in six.iteritems(self.details):
            details[key] = value
        return str(self.message.format(**details))


class HookError(Error):
    pass


class InvalidCallbackError(HookError):
    default_message = "Invalid callback '{callback}' provided for '{hook_name}' hook"


class CallbackExecutionError(HookError):
    default_message = "Failed to execute callback '{callback}' for hook '{hook_name}'. {exc_msg}"


class HookNotFoundError(HookError):
    default_message = "Unable to find a hook '{hook_name}'"


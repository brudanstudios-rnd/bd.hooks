import logging

LOGGER = logging.getLogger(__name__)


class HookExecutor(object):

    def __init__(self, hook_items, *args, **kwargs):
        self._hook_items = hook_items
        self._args = args
        self._kwargs = kwargs

    def all(self, result_callback=None):
        for hook_item in self._hook_items:

            result = hook_item.execute(*self._args, **self._kwargs)

            if result_callback:
                result_callback(result)

    def one(self):
        return self._hook_items[0].execute(*self._args, **self._kwargs)
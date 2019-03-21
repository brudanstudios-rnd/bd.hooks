__all__ = ["HookLoader"]

import os
import logging

from pluginbase import PluginBase

from .exceptions import *

LOGGER = logging.getLogger(__name__)


def get_searchpath(path):

    paths = [path]

    for entry in os.listdir(path):
        entry_path = os.path.join(path, entry)
        if not os.path.isdir(entry_path):
            continue

        paths.extend(get_searchpath(entry_path))

    return paths


class HookLoader(object):

    _plugin_source = None

    @classmethod
    def load(cls, registry, hook_search_paths=None):
        if hook_search_paths is None:
            hook_search_paths = []

        hook_search_paths = map(str, hook_search_paths)

        BD_HOOKPATH = os.getenv("BD_HOOKPATH")
        if BD_HOOKPATH:
            hook_search_paths.extend(BD_HOOKPATH.split(os.pathsep))

        if not hook_search_paths:
            LOGGER.warning(
                'Hook search paths are not provided. '
                'Check if \'BD_HOOKPATH\' environment variable exists'
            )
            return

        existing_hook_search_paths = filter(os.path.exists, hook_search_paths)

        if not existing_hook_search_paths:
            LOGGER.warning(
                'There are no existing search paths in the list: {}'.format(
                    existing_hook_search_paths
                )
            )
            return

        deep_search_paths = []
        for hook_search_path in existing_hook_search_paths:
            try:
                deep_search_paths.extend(get_searchpath(hook_search_path))
            except OSError as e:
                LOGGER.warning(
                    'There are some os errors on search path lookup: {}'.format(str(e))
                )
                continue

        if not deep_search_paths:
            return

        plugin_base = PluginBase(package="bd_hooks")

        cls._plugin_source = plugin_base.make_plugin_source(searchpath=deep_search_paths)

        for plugin_name in cls._plugin_source.list_plugins():
            try:
                plugin = cls._plugin_source.load_plugin(plugin_name)
            except Exception as e:
                LOGGER.warning(
                    'Hook \'{path}\' failed to load. {exc_msg}'.format(
                        path=plugin_name,
                        exc_msg=str(e)
                    )
                )
                continue

            if not hasattr(plugin, 'register'):
                LOGGER.warning('Missing \'register\' function in module \'{}\''.format(plugin_name))
                continue

            try:
                plugin.register(registry)
            except Exception as e:
                LOGGER.warning(
                    'Failed to register hook from \'{path}\'. {exc_msg}'.format(
                        path=plugin_name,
                        exc_msg=str(e)
                    )
                )

    @classmethod
    def clean(cls):
        cls._plugin_source = None
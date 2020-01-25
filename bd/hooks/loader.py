import os
import logging

from .vendor.pluginbase import PluginBase

LOGGER = logging.getLogger(__name__)


def get_searchpath(root_dir):
    """Return a list of all subdirectories under the root directory.

    This function goes to every subdirectory recursively and appends
    it path to the resulting list.

    Args:
        root_dir (str): A parent directory.

    Returns:
        list[str]: A list of subdirectories including the root directory.

    """
    paths = [root_dir]

    for entry in os.listdir(root_dir):
        entry_path = os.path.join(root_dir, entry)
        if not os.path.isdir(entry_path):
            continue

        paths.extend(get_searchpath(entry_path))

    return paths


def load(registry, hook_search_paths=None):
    """Find and register all the available hooks.

    Args:
        registry (bd.hooks.registry.HookRegistry): Plugin registry object.
        hook_search_paths (list[str]): A list of initial folders to search plugins at.

    """
    if hook_search_paths is None:
        hook_search_paths = []

    # convert all search paths to strings
    hook_search_paths = list(map(str, hook_search_paths))

    # extract search paths from environment variable
    BD_HOOKPATH = os.getenv("BD_HOOKPATH")
    if BD_HOOKPATH:
        hook_search_paths.extend(BD_HOOKPATH.split(os.pathsep))

    if not hook_search_paths:
        LOGGER.warning(
            'Hook search paths are not provided. '
            'Check if \'BD_HOOKPATH\' environment variable exists'
        )
        return

    # keep only existing search paths
    existing_hook_search_paths = list(filter(os.path.exists, hook_search_paths))

    if not existing_hook_search_paths:
        LOGGER.warning(
            'There are no existing search paths in the list: {}'.format(
                existing_hook_search_paths
            )
        )
        return

    # recursively find all the search subdirectories
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

    plugin_base = PluginBase(package="bd.hooks")

    plugin_source = plugin_base.make_plugin_source(
        searchpath=deep_search_paths,
        persist=True
    )

    for plugin_name in plugin_source.list_plugins():
        try:
            plugin = plugin_source.load_plugin(plugin_name)
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

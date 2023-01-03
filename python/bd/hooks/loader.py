import os
import logging

import importlib.machinery
import importlib.util

logger = logging.getLogger(__name__)


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


def load(registry, hook_search_paths):
    """Find and register all the available hooks.

    Args:
        registry (bd.hooks.registry.HookRegistry): Plugin registry object.
        hook_search_paths (list[str]): A list of initial folders to search plugins at.

    """
    if not hook_search_paths:
        logger.warning("Hook search paths are not provided.")
        return

    # keep only existing search paths
    existing_hook_search_paths = list(filter(os.path.exists, hook_search_paths))

    if not existing_hook_search_paths:
        logger.warning(
            "There is no existing search paths in the list: {}".format(
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
            logger.warning(
                "There are some os errors on search path lookup: {}".format(str(e))
            )
            continue

    if not deep_search_paths:
        return

    for hook_search_path in deep_search_paths:

        for filename in os.listdir(hook_search_path):

            if not filename.endswith(".py"):
                continue

            module_path = os.path.join(hook_search_path, filename)

            module_name = filename.rsplit(".", 1)[0]

            loader = importlib.machinery.SourceFileLoader(module_name, module_path)

            spec = importlib.util.spec_from_loader(module_name, loader)
            if not spec:
                continue

            module = importlib.util.module_from_spec(spec)

            try:
                loader.exec_module(module)
            except Exception as e:
                logger.warning(
                    "Hook '{path}' failed to load. {exc_msg}".format(
                        path=module_path, exc_msg=str(e)
                    )
                )
                continue

            if not hasattr(module, "register"):
                logger.warning(
                    "Missing 'register' function in '{}'".format(module_path)
                )
                continue

            try:
                module.register(registry)
            except Exception as e:
                logger.exception(
                    "Failed to register hook from '{path}'. {exc_msg}".format(
                        path=module_path, exc_msg=str(e)
                    )
                )

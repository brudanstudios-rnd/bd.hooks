import os
import logging
from bd import hooks

import pytest
import mock


@pytest.fixture
def clean_module():
    hooks._registry = None
    return


class LoadTests:

    @mock.patch('bd.hooks.loader.load', spec_set=True)
    @mock.patch('bd.hooks.registry.HookRegistry', spec_set=True)
    def test_loads_only_once(self, mock_registry_init, mock_hookload, clean_module):
        mock_registry = mock.Mock()
        mock_registry_init.return_value = mock_registry

        hooks.load()

        mock_registry_init.assert_called_once()
        mock_hookload.assert_called_once_with(mock_registry, None)
        assert hooks._registry is mock_registry

        hooks.load()

        mock_registry_init.assert_called_once()
        mock_hookload.assert_called_once()
        assert hooks._registry is mock_registry


def test_successfully_loads_and_executes_hooks(temp_dir_creator, clean_module, caplog):
    search_paths = [temp_dir_creator(), temp_dir_creator()]

    plugin_path = os.path.join(search_paths[0], 'plugin_0.py')
    with open(plugin_path, 'w') as f:
        # making mistake in function name
        f.write(
            '\n'
            'def action_1():\n'
            '    return "action_1"\n'
            '\n'
            'def register(registry):\n'
            '    registry.add_hook("test_hook", action_1)\n'
        )

    plugin_path = os.path.join(search_paths[1], 'plugin_1.py')
    with open(plugin_path, 'w') as f:
        f.write(
            '\n'
            'class Hook(object):\n'
            '    def action_2(self):\n'
            '        return "action_2"\n'
            '\n'
            '\n'
            'def register(registry):\n'
            '    hook = Hook()\n'
            '    registry.add_hook("test_hook", hook.action_2)\n'
        )

    hooks.load(search_paths)

    caplog.set_level(logging.DEBUG, logger=bd.hooks.registry.LOGGER.name)

    hook_items = hooks._registry.get_hooks('test_hook')

    for record in caplog.records:
        assert record.levelname != 'ERROR'

    assert len(hook_items) == 2

    executor = hooks.execute('test_hook')

    mock_result_callback = mock.Mock()
    executor.all(mock_result_callback)

    mock_result_callback.assert_has_calls([mock.call('action_1'), mock.call('action_2')], any_order=True)
import os
import bd_hooks

import pytest
import mock


@pytest.fixture
def clean_module():
    bd_hooks._registry = None
    return


class LoadTests:

    @mock.patch('bd_hooks.HookLoader', spec_set=True)
    @mock.patch('bd_hooks.HookRegistry', spec_set=True)
    def test_loads_only_once(self, mock_registry_init, mock_hookloader, clean_module):
        mock_registry = mock.Mock()
        mock_registry_init.return_value = mock_registry

        bd_hooks.load()

        mock_registry_init.assert_called_once()
        mock_hookloader.load.assert_called_once_with(mock_registry, None)
        assert bd_hooks._registry is mock_registry

        bd_hooks.load()

        mock_registry_init.assert_called_once()
        mock_hookloader.load.assert_called_once()
        assert bd_hooks._registry is mock_registry


def test_successfully_loads_and_executes_hooks(temp_dir_creator, clean_module):
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
            'def action_2():\n'
            '    return "action_2"\n'
            '\n'
            'def register(registry):\n'
            '    registry.add_hook("test_hook", action_2)\n'
        )

    bd_hooks.load(search_paths)

    hook_items = bd_hooks._registry.get_hooks('test_hook')
    assert len(hook_items) == 2

    executor = bd_hooks.execute('test_hook')

    mock_result_callback = mock.Mock()
    executor.all(mock_result_callback)

    mock_result_callback.assert_has_calls([mock.call('action_1'), mock.call('action_2')], any_order=True)
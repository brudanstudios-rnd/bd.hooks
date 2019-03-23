import types
import copy

import pytest
import mock

from bd_hooks import registry
from bd_hooks import exceptions


@pytest.fixture(scope='function')
def hook_registry():
    return registry.HookRegistry()


class HookRegistryTests:

    class AddHookTests:

        @mock.patch(
            'bd_hooks.registry.InvalidCallbackError',
            side_effect=exceptions.InvalidCallbackError
        )
        def test_raises_error_on_invalid_provided_callback(self, mock_error, hook_registry):
            with pytest.raises(exceptions.InvalidCallbackError):
                hook_registry.add_hook('test_hook', 'non-callable-argument')

            mock_error.assert_called_once()
            mock_error.assert_called_once_with(details={'hook_name': 'test_hook', 'callback': 'non-callable-argument'})

        @mock.patch('bd_hooks.registry.HookItem')
        def test_adds_hook(self, mock_hook_init, hook_registry):
            mock_hook_item = mock.Mock(spec_set=registry.HookItem)
            mock_hook_init.return_value = mock_hook_item

            mock_callback = mock.Mock()
            hook_registry.add_hook('test_hook', mock_callback)

            mock_hook_init.assert_called_once_with('test_hook', mock_callback, 50)
            assert 'test_hook' in hook_registry._data
            assert hook_registry._data['test_hook'] == [mock_hook_item]

        @mock.patch('bd_hooks.registry.HookItem')
        def test_passes_correct_priority_to_hook_item(self, mock_hook_init, hook_registry):
            mock_hook_item = mock.Mock()
            mock_hook_init.return_value = mock_hook_item

            mock_callback = mock.Mock(spec=types.FunctionType)
            hook_registry.add_hook('test_hook', mock_callback, 75)

            assert 'test_hook' in hook_registry._data
            assert hook_registry._data['test_hook'] == [mock_hook_item]
            mock_hook_init.assert_called_once_with('test_hook', mock_callback, 75)


    class GetHooksTests:

        def test_returns_hooks_on_name_found(self, hook_registry):

            class MockHookItem(object):
                @property
                def priority(self):
                    return 50

            hooks = []
            for i in range(3):
                mock_hook_item = MockHookItem()
                hooks.append(mock_hook_item)

            hook_registry._data['test_hooks'] = hooks[:]

            result = hook_registry.get_hooks('test_hooks')

            assert all([hook in hooks for hook in result])

        def test_raises_error_on_no_hooks_found(self, hook_registry):
            with pytest.raises(exceptions.HookNotFoundError):
                hook_registry.get_hooks('non-existing-hook')

        def test_returns_sorted_hooks_on_name_found(self, hook_registry):
            class MockHookItem:
                def __init__(self, priority):
                    self._priority = priority

                @property
                def priority(self):
                    return self._priority

            hooks = []
            for i in range(1, 4):
                mock_hook_item = MockHookItem(i * 50)
                hooks.append(mock_hook_item)

            hook_registry._data['test_hooks'] = copy.copy(hooks)

            expected = list(reversed(hooks))
            actual = hook_registry.get_hooks('test_hooks')

            # check descending priority order
            assert all([a is b for a, b in zip(actual, expected)])

        def test_cached_sorting(self, hook_registry):
            hooks = mock.Mock(spec=list)

            hook_registry._data['test_hooks_1'] = hooks

            hook_registry.get_hooks('test_hooks_1')
            hook_registry.get_hooks('test_hooks_1')

            hooks.sort.assert_called_once()

            # check with the other hook name

            hooks = mock.Mock(spec=list)

            hook_registry._data['test_hooks_2'] = hooks

            hook_registry.get_hooks('test_hooks_2')
            hook_registry.get_hooks('test_hooks_2')

            hooks.sort.assert_called_once()


class HookItemTests:

    class ConstructorTests:

        def test_correctly_stores_callback(self):
            mock_callback = mock.Mock()
            hook_item = registry.HookItem('test_hook', mock_callback)

            assert isinstance(hook_item, registry.HookItem)
            assert hook_item._name == 'test_hook'
            assert hook_item._callback is mock_callback

    class ExecuteTests:

        def test_executes_callback_with_correct_arguments(self):
            mock_callback = mock.Mock(return_value=42)
            hook_item = registry.HookItem('test_hook', mock_callback)

            assert hook_item._callback is mock_callback
            assert hook_item.execute('arg_1', 'arg_2', kwarg_1='kwarg_1', kwarg_2='kwarg_2') == 42
            hook_item._callback.assert_called_once_with('arg_1', 'arg_2', kwarg_1='kwarg_1', kwarg_2='kwarg_2')

        def test_raises_error_on_failed_callback(self):
            mock_callback = mock.Mock()
            mock_callback.side_effect = Exception

            hook_item = registry.HookItem('test_hook', mock_callback)

            with pytest.raises(registry.CallbackExecutionError):
                hook_item.execute()

        def test_keeps_reference_to_deleted_method_owner(self):
            class MockHookClass(object):

                def __init__(self):
                    self._data = [0, 1, 2]

                def execute(self):
                    return self._data

            mock_hook = MockHookClass()

            hook_item = registry.HookItem('test_hook', mock_hook.execute)

            del mock_hook

            try:
                hook_item.execute()
            except exceptions.CallbackExecutionError:
                pytest.fail('Raises error when it shouldn\'t')

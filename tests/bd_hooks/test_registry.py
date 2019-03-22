import types
import copy
import weakref

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

        @mock.patch('bd_hooks.registry.HookItem.create')
        def test_adds_hook(self, mock_hook_create, hook_registry):
            mock_hook_item = mock.Mock(spec_set=registry.HookFunctionItem)
            mock_hook_create.return_value = mock_hook_item

            mock_callback = mock.Mock(spec=types.FunctionType)
            hook_registry.add_hook('test_hook', mock_callback)

            mock_hook_create.assert_called_once_with('test_hook', mock_callback, 50)
            assert 'test_hook' in hook_registry._hooks
            assert hook_registry._hooks['test_hook'] == [mock_hook_item]

        @mock.patch('bd_hooks.registry.HookItem.create')
        def test_passes_correct_priority_to_hook_item(self, mock_hook_create, hook_registry):
            mock_hook_item = mock.Mock()
            mock_hook_create.return_value = mock_hook_item

            mock_callback = mock.Mock(spec=types.FunctionType)
            hook_registry.add_hook('test_hook', mock_callback, 75)

            assert 'test_hook' in hook_registry._hooks
            assert hook_registry._hooks['test_hook'] == [mock_hook_item]
            mock_hook_create.assert_called_once_with('test_hook', mock_callback, 75)


    class GetHooksTests:

        @mock.patch.object(registry.HookRegistry, '_cleanup', spec=True)
        def test_returns_hooks_on_name_found(self, mock_cleanup, hook_registry):

            class MockHookItem(object):
                @property
                def priority(self):
                    return 50

            hooks = []
            for i in range(3):
                mock_hook_item = MockHookItem()
                hooks.append(mock_hook_item)

            hook_registry._hooks['test_hooks'] = hooks[:]

            result = hook_registry.get_hooks('test_hooks')

            assert all([hook in hooks for hook in result])

        def test_raises_error_on_no_hooks_found(self, hook_registry):
            with pytest.raises(exceptions.HookNotFoundError):
                hook_registry.get_hooks('non-existing-hook')

        @mock.patch.object(registry.HookRegistry, '_cleanup', spec=True)
        def test_returns_sorted_hooks_on_name_found(self, mock_cleanup, hook_registry):
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

            hook_registry._hooks['test_hooks'] = copy.copy(hooks)

            expected = list(reversed(hooks))
            actual = hook_registry.get_hooks('test_hooks')

            # check descending priority order
            assert all([a is b for a, b in zip(actual, expected)])

        @mock.patch.object(registry.HookRegistry, '_cleanup', spec=True)
        def test_cached_sorting(self, mock_cleanup, hook_registry):
            hooks = mock.Mock(spec=list)

            hook_registry._hooks['test_hooks_1'] = hooks

            hook_registry.get_hooks('test_hooks_1')
            hook_registry.get_hooks('test_hooks_1')

            hooks.sort.assert_called_once()

            # check with the other hook name

            hooks = mock.Mock(spec=list)

            hook_registry._hooks['test_hooks_2'] = hooks

            hook_registry.get_hooks('test_hooks_2')
            hook_registry.get_hooks('test_hooks_2')

            hooks.sort.assert_called_once()


    class CleanupTests:

        def test_removes_method_bound_to_dead_objects(self, hook_registry):
            mock_hook_item_1 = mock.Mock()
            mock_hook_item_1.is_valid.return_value = True

            mock_hook_item_2 = mock.Mock()
            mock_hook_item_2.is_valid.return_value = False

            mock_hook_item_3 = mock.Mock()
            mock_hook_item_3.is_valid.return_value = True

            hook_registry._hooks['test_hooks'] = [mock_hook_item_1, mock_hook_item_2, mock_hook_item_3]

            hook_registry._cleanup('test_hooks')

            assert 'test_hooks' in hook_registry._hooks
            assert hook_registry._hooks['test_hooks'] == [mock_hook_item_1, mock_hook_item_3]

        def test_raises_error_when_all_hooks_for_current_name_are_deleted(self, hook_registry):
            mock_hook_item_1 = mock.Mock()
            mock_hook_item_1.is_valid.return_value = False

            hook_registry._hooks['test_hooks'] = [mock_hook_item_1]
            hook_registry._sorted.add('test_hooks')

            with pytest.raises(registry.HookCallbackDeadError):
                hook_registry._cleanup('test_hooks')

            assert 'test_hooks' not in hook_registry._hooks
            assert 'test_hooks' not in hook_registry._sorted


class HookItemTests:

    class ConstructorTests:

        def test_correctly_stores_function(self):
            mock_callback = mock.Mock(spec=types.FunctionType)
            hook_item = registry.HookItem.create('test_hook', mock_callback)

            assert isinstance(hook_item, registry.HookFunctionItem)
            assert hook_item._name == 'test_hook'
            assert hook_item._callback is mock_callback

        @mock.patch('bd_hooks.registry.six.get_method_function', autospec=True)
        @mock.patch('bd_hooks.registry.six.get_method_self', autospec=True)
        def test_correctly_stores_method(self, mock_self, mock_func):
            mock_hook = mock.Mock()
            mock_hook.method = mock.Mock(spec=types.MethodType)

            mock_method_function = mock.Mock()

            mock_func.return_value = mock_method_function
            mock_self.return_value = mock_hook

            hook_item = registry.HookItem.create('test_hook', mock_hook.method)

            assert isinstance(hook_item, registry.HookMethodItem)
            assert hook_item._callback is mock_method_function
            assert hook_item._obj_weakref is weakref.ref(mock_hook)

    class ExecuteTests:

        def test_calls_function_with_correct_arguments(self):
            mock_callback = mock.Mock(spec=types.FunctionType, return_value=42)
            hook_item = registry.HookItem.create('test_hook', mock_callback)

            assert hook_item._callback is mock_callback
            assert hook_item.execute('arg_1', 'arg_2', kwarg_1='kwarg_1', kwarg_2='kwarg_2') == 42
            hook_item._callback.assert_called_once_with('arg_1', 'arg_2', kwarg_1='kwarg_1', kwarg_2='kwarg_2')

        @mock.patch('bd_hooks.registry.six.get_method_function', autospec=True)
        @mock.patch('bd_hooks.registry.six.get_method_self', autospec=True)
        def test_calls_method_with_correct_arguments(self, mock_self, mock_func):
            expected_args = ('arg_1', 'arg_2')
            expected_kwargs = dict(kwarg_1='kwarg_1', kwarg_2='kwarg_2')

            mock_hook = mock.Mock()
            mock_hook.method = mock.Mock(spec=types.MethodType)

            mock_method_function = mock.Mock(return_value=42)

            mock_func.return_value = mock_method_function
            mock_self.return_value = mock_hook

            hook_item = registry.HookItem.create('test_hook', mock_hook.method)

            assert hook_item._obj_weakref is not None
            assert hook_item._obj_weakref is weakref.ref(mock_hook)
            assert hook_item.execute(*expected_args, **expected_kwargs) == 42
            mock_method_function.assert_called_once_with(mock_hook, *expected_args, **expected_kwargs)

        @mock.patch('bd_hooks.registry.six.get_method_function', autospec=True)
        @mock.patch('bd_hooks.registry.six.get_method_self', autospec=True)
        def test_raises_error_on_failed_callback(self, mock_self, mock_func):
            mock_function = mock.Mock(spec=types.FunctionType)
            mock_function.side_effect = Exception

            hook_item = registry.HookItem.create('test_hook', mock_function)

            with pytest.raises(registry.CallbackExecutionError):
                hook_item.execute()

            mock_method = mock.Mock(spec=types.MethodType)

            mock_func.return_value = mock.Mock(side_effect=Exception)
            mock_self.return_value = mock.Mock()

            hook_item = registry.HookItem.create('test_hook', mock_method)

            with pytest.raises(registry.CallbackExecutionError):
                hook_item.execute()

        def test_raises_error_on_deleted_method_owner(self):
            class MockHookClass(object):

                def __init__(self):
                    self._data = [0, 1, 2]

                def execute(self):
                    return self._data

            mock_hook = MockHookClass()

            hook_item = registry.HookItem.create('test_hook', mock_hook.execute)

            del mock_hook

            with pytest.raises(exceptions.CallbackExecutionError):
                hook_item.execute()

    class IsValidTests:

        def test_detects_deleted_method_owner(self):
            class MockHookClass(object):

                def __init__(self):
                    self._data = [0, 1, 2]

                def execute(self):
                    return self._data

            mock_hook = MockHookClass()

            hook_item = registry.HookItem.create('test_hook', mock_hook.execute)

            assert hook_item.is_valid() is True

            del mock_hook

            assert hook_item.is_valid() is False

        def test_detect_when_function_callback_is_none(self):

            mock_function = mock.Mock(spec=types.FunctionType)
            hook_item = registry.HookItem.create('test_hook', mock_function)
            assert hook_item.is_valid() is True

            hook_item = registry.HookItem.create('test_hook', None)
            assert hook_item.is_valid() is False

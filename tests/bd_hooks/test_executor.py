import bd_hooks
from bd_hooks.exceptions import CallbackExecutionError
from bd_hooks.executor import HookExecutor

import pytest
import mock

class HookExecutorTests:

    class OneTests:

        def test_executes_first_item(self):
            hook_items = [
                mock.Mock(spec_set=bd_hooks.registry.HookItem),
                mock.Mock(spec_set=bd_hooks.registry.HookItem),
                mock.Mock(spec_set=bd_hooks.registry.HookItem)
            ]
            hook_executor = HookExecutor(hook_items)

            hook_executor.one()

            hook_items[0].execute.assert_called_once()
            hook_items[1].execute.assert_not_called()
            hook_items[2].execute.assert_not_called()

        def test_passes_correct_arguments(self):
            hook_items = [mock.Mock(spec_set=bd_hooks.registry.HookItem)]
            hook_executor = HookExecutor(hook_items, 'a', 'b', a='a', b='b')

            hook_executor.one()

            hook_items[0].execute.assert_called_once_with('a', 'b', a='a', b='b')

        def test_raises_error_on_execute_fail(self):
            mock_hook_item = mock.Mock(spec_set=bd_hooks.registry.HookItem)
            mock_hook_item.execute.side_effect = Exception

            hook_executor = HookExecutor([mock_hook_item])

            with pytest.raises(Exception):
                hook_executor.one()

    class AllTests:

        def test_executes_all_items(self):
            hook_items = [
                mock.Mock(spec_set=bd_hooks.registry.HookItem),
                mock.Mock(spec_set=bd_hooks.registry.HookItem),
                mock.Mock(spec_set=bd_hooks.registry.HookItem)
            ]
            hook_executor = HookExecutor(hook_items)

            hook_executor.all()

            for hook_item in hook_items:
                hook_item.execute.assert_called_once()

        def test_passes_correct_arguments(self):
            hook_items = [mock.Mock(spec_set=bd_hooks.registry.HookItem)]
            hook_executor = HookExecutor(hook_items, 'a', 'b', a='a', b='b')

            hook_executor.all()

            hook_items[0].execute.assert_called_once_with('a', 'b', a='a', b='b')

        def test_calls_result_callback(self):
            mock_hook_item = mock.Mock(spec_set=bd_hooks.registry.HookItem)
            mock_hook_item.execute.side_effect = ['a', 'b', 'c']
            hook_executor = HookExecutor([mock_hook_item, mock_hook_item, mock_hook_item])

            mock_result_callback = mock.Mock()

            hook_executor.all(mock_result_callback)

            mock_result_callback.assert_has_calls(
                [mock.call('a'), mock.call('b'), mock.call('c')]
            )

        def test_raises_error_on_execute_fail(self):
            mock_hook_item = mock.Mock(spec_set=bd_hooks.registry.HookItem)
            mock_hook_item.execute.side_effect = CallbackExecutionError(
                details={
                    'hook_name': 'test_hook',
                    'callback': 'test_callback',
                    'exc_msg': 'test_exception'
                }
            )

            hook_executor = HookExecutor([mock_hook_item])

            with pytest.raises(CallbackExecutionError):
                hook_executor.all()

        @mock.patch(
            'bd_hooks.registry.CallbackExecutionError',
            side_effect=Exception
        )
        def test_suppresses_error_when_safe_execute_is_true(self, mock_exception):
            mock_hook_item = mock.Mock(spec_set=bd_hooks.registry.HookItem)
            mock_hook_item.execute.side_effect = [
                'result',
                CallbackExecutionError(
                    details={
                        'hook_name': 'test_hook',
                        'callback': 'test_callback',
                        'exc_msg': 'test_exception'
                    }
                )
            ]

            hook_executor = HookExecutor([mock_hook_item, mock_hook_item])

            try:
                hook_executor.all(safe_execute=True)
            except CallbackExecutionError:
                pytest.fail('the exception is raised when it shouldn\'t have been')
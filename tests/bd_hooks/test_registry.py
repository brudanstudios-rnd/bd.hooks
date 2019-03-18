import types

import pytest
import mock

from bd_hooks import registry
from bd_hooks import exceptions


class MockError(Exception):

    def __init__(self, message=None, details=None):
        pass


class AddHookTests:

    @mock.patch(
        'bd_hooks.registry.InvalidCallbackError',
        side_effect=exceptions.InvalidCallbackError
    )
    def test_raises_error_on_invalid_provided_callback(self, mock_error):
        hook_registry = registry.HookRegistry()
        with pytest.raises(exceptions.InvalidCallbackError):
            hook_registry.add_hook('test_hook', 'non-callable-argument')

        mock_error.assert_called_once()
        mock_error.assert_called_once_with(details={'hook_name': 'test_hook', 'callback': 'non-callable-argument'})

    def test_add_new_hook_with_default_arguments(self):
        hook_registry = registry.HookRegistry()

        mock_callback = mock.Mock(spec=types.FunctionType)
        hook_registry.add_hook('test_hook', mock_callback)

        assert 'test_hook' in hook_registry._hooks
        assert hook_registry._hooks['test_hook'] == [(50, mock_callback, None)]

    def
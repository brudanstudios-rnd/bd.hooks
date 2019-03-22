from bd_hooks.exceptions import Error


class ErrorTests:

    class InitTests:

        def test_uses_default_message_on_no_custom_message_provided(self):
            error = Error()
            assert error.message == error.default_message

        def test_uses_custom_message_if_provided(self):
            expected_message = 'custom message'
            error = Error(expected_message)
            assert error.message == expected_message

        def test_stores_formatted_traceback(self):
            try:
                try:
                    raise Exception()
                except Exception as e:
                    raise Error()
            except Error as e:
                assert e.traceback.startswith('Traceback (most recent call last):')
                assert e.traceback.endswith('raise Exception()\nException\n')

        def test_stores_details_if_provided(self):
            error = Error()
            assert error.details == {}

            error = Error(details=dict(a='a', b='b'))
            assert error.details == dict(a='a', b='b')

    class StrTests:

        def test_uses_details_to_format_message(self):
            class ErrorSubclass(Error):
                default_message = 'message: {msg}, data: {data}'

            error = ErrorSubclass(details=dict(msg='hello', data='world'))
            assert str(error) == 'message: hello, data: world'
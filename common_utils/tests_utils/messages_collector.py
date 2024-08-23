from typing import Callable, Optional, Collection

from aiogram.types import Message


def messages_collector(expected_types: Optional[list] = None) -> Callable:
    """
    This is the decorator that collects messages from aiogram method
    Used to test the methods

    :param expected_types: the argument used when this decorator is being applied to handler
    """

    def _messages_collector(func: Callable) -> Callable:
        async def wrapper_func(*args, is_unit_test: bool = True, **kwargs) -> list[Message]:
            """

            :param args: arguments for the method
            :param is_unit_test: True if method is considered a unit test
                otherwise the test is considired to be an integration test
            :param kwargs: parametered arguments for the method
            """
            if not is_unit_test:
                return []

            if expected_types:
                kwargs = {key: value for key, value in filter(lambda x: type(x[1]) in expected_types, kwargs.items())}

            messages = []
            async for result in func(*args, **kwargs):
                if isinstance(result, Collection):
                    messages.extend(result)  # TODO come up with is_unit_test
                else:
                    messages.append(result)

            return messages

        return wrapper_func

    return _messages_collector

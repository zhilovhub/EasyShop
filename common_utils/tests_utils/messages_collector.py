from typing import Callable, Optional, Any

from aiogram.types import Message


def messages_collector(expected_types: Optional[list] = None) -> Callable:
    """
    This is the decorator that collects messages from aiogram method
    Used to test the methods

    :param expected_types: the argument used when this decorator is being applied to handler
    """

    def _messages_collector(func: Callable) -> Callable:
        async def wrapper_func(*args, **kwargs) -> tuple[Any, list[Message]]:
            """

            :param args: arguments for the method
            :param kwargs: parametered arguments for the method
            """
            if expected_types:  # Custom Dependency Injection (not to provide arguments that function doesn't expect)
                kwargs = {key: value for key, value in filter(lambda x: type(x[1]) in expected_types, kwargs.items())}

            returned_value = None
            messages = []

            async for result in func(*args, **kwargs):
                if isinstance(result, Message):  # case №1
                    messages.append(result)
                elif isinstance(result, list):  # case №2
                    messages.extend(result)
                elif isinstance(result, tuple):  # case №3
                    returned_value = result[0]
                    messages.extend(result[1])
                else:
                    returned_value = result  # case №4

            return (returned_value, messages)

        return wrapper_func

    return _messages_collector


"""
example

@message_collector()
async def function_to_test():
    yield await bot.send_message(...)  # case №1
    yield await bot.send_message(...)  # case №1

    yield await bot.method_that_returns_nothing_but_sends_messages(...)  # case №2
    
    result, messages = await bot.method_returns_something_and_sends_messages(...)
    yield messages  # case №3

    if result > 5:
        print("function ends")
        return  # will return nothing to @message_collector(), it is just to end the function
    else:
        yield True  # case №4
"""  # noqa

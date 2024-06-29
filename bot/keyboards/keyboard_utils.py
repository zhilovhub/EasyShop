from logs.config import logger


def callback_json_validator(func):
    def wrapper_func(*args, **kwargs):
        callback_json = func(*args, **kwargs)

        if len(callback_json) > 64:
            logger.warning(f"The callback {callback_json} has len ({len(callback_json)}) more than 64")

        return callback_json

    return wrapper_func

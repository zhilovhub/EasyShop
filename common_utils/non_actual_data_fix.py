from pydantic import ValidationError

from logs.config import logger


def non_actual_data_fix(data: dict, e: ValidationError) -> dict:
    """
    It is used when user tries to make an action with old data
    :raises ValidationError:
    """
    error_dict = e.errors()
    logger.warning(f"{len(error_dict)} errors have been found due to old data: {data}", exc_info=e)

    for error in error_dict:
        error_type = error["type"]
        data_key = error["loc"][0]
        input_value = error["input"]

        match error_type:
            case "string_type":
                data[data_key] = str(input_value)
            case _:
                raise e

    return data

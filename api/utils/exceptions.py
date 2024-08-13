from fastapi import HTTPException


RESPONSES_DICT = {  # keep it sorted by keys
    400: {"description": "Bad request (incorrect input data)."},
    404: {"description": "Item not found."},
    406: {"description": "Custom bot is offline."},
    409: {"description": "Conflict."},
    415: {"description": "Unaccepted File Type."},
    401: {"description": "Unauthorized."},
    500: {"description": "Internal server error."},
}


def _generate_extra_params_text(**extra_params):
    return_text = ""
    if extra_params:
        return_text += ' extra params: '
        for k, v in extra_params.items():
            if v:
                return_text += f"{k}={v} "
    return return_text


class SearchWordMustNotBeEmptyError(Exception):
    """Raised when 'search' filter is provided but search word is empty string"""


class HTTPBadRequestError(HTTPException):
    """Raised when Bad request error occurred: status 400"""

    def __init__(self, detail_message: str = RESPONSES_DICT[400]['description'], **extra_params):
        self.status_code = 400
        self.detail = detail_message + _generate_extra_params_text(**extra_params)
        super().__init__(status_code=self.status_code, detail=self.detail)


class HTTPUnauthorizedError(HTTPException):
    """Raised when Bad request error occurred: status 400"""

    def __init__(self, detail_message: str = RESPONSES_DICT[401]['description'], **extra_params):
        self.status_code = 401
        self.detail = detail_message + _generate_extra_params_text(**extra_params)
        super().__init__(status_code=self.status_code, detail=self.detail)


class HTTPUnacceptedError(HTTPException):
    """Raised when Unaccepted error occurred: status 415"""

    def __init__(self, detail_message: str = RESPONSES_DICT[415]['description'], **extra_params):
        self.status_code = 415
        self.detail = detail_message + _generate_extra_params_text(**extra_params)
        super().__init__(status_code=self.status_code, detail=self.detail)


class HTTPCustomBotIsOfflineError(HTTPException):
    """Raised when Conflict error occurred: status 406"""

    def __init__(self, detail_message: str = RESPONSES_DICT[406]['description'], **extra_params):
        self.status_code = 406
        self.detail = detail_message + _generate_extra_params_text(**extra_params)
        super().__init__(status_code=self.status_code, detail=self.detail)


class HTTPConflictError(HTTPException):
    """Raised when Conflict error occurred: status 409"""

    def __init__(self, detail_message: str = RESPONSES_DICT[409]['description'], **extra_params):
        self.status_code = 409
        self.detail = detail_message + _generate_extra_params_text(**extra_params)
        super().__init__(status_code=self.status_code, detail=self.detail)


class HTTPInternalError(HTTPException):
    """Raised when unknown internal server error occurred: status 500"""

    def __init__(self, detail_message: str = RESPONSES_DICT[500]['description'], **extra_params):
        self.status_code = 500
        self.detail = detail_message + _generate_extra_params_text(**extra_params)
        super().__init__(status_code=self.status_code, detail=self.detail)


class HTTPItemNotFoundError(HTTPException):
    """Raised when item not found in database"""

    def __init__(self, detail_message: str = RESPONSES_DICT[404]['description'], **extra_params):
        self.status_code = 404
        self.detail = detail_message + _generate_extra_params_text(**extra_params)
        super().__init__(status_code=self.status_code, detail=self.detail)


class HTTPProductNotFoundError(HTTPItemNotFoundError):
    def __init__(self, product_id: int | None = None, bot_id: int | None = None):
        super().__init__(detail_message="Product not found.", product_id=product_id, bot_id=bot_id)


class HTTPBotNotFoundError(HTTPItemNotFoundError):
    def __init__(self, bot_id: int | None = None):
        super().__init__(detail_message="Bot not found.", bot_id=bot_id)


class HTTPCategoryNotFoundError(HTTPItemNotFoundError):
    def __init__(self, category_id: int | None = None, bot_id: int | None = None):
        super().__init__(detail_message="Category not found.", category_id=category_id, bot_id=bot_id)


class HTTPFileNotFoundError(HTTPItemNotFoundError):
    def __init__(self, file_name: str | None = None):
        super().__init__(detail_message="File not found.", file_name=file_name)

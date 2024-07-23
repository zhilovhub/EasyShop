from fastapi import HTTPException


RESPONSES_DICT = {
    404: {"description": "Item not found"},
    400: {"description": "Bad request (incorrect input data)"},
    409: {"description": "Conflict"},
    500: {"description": "Internal server error"},
    406: {"description": "Custom bot is offline"}
}


def _generate_extra_params_text(**extra_params):
    return_text = ""
    if extra_params:
        return_text += ' extra params: '
        for k, v in extra_params.items():
            if v:
                return_text += f"{k}={v} "
    return return_text


class SearchWordMustNotBeEmpty(Exception):
    """Raised when 'search' filter is provided but search word is empty string"""
    pass


class HTTPInternalError(HTTPException):
    """Raised when unknown internal server error occurred"""

    def __init__(self, detail_message: str = RESPONSES_DICT[500]['description'], **extra_params):
        self.status_code = 500
        self.detail = detail_message + _generate_extra_params_text(**extra_params)
        super().__init__(status_code=self.status_code, detail=self.detail)


class HTTPBadRequest(HTTPException):
    """Raised when Bad request error occurred"""

    def __init__(self, detail_message: str = RESPONSES_DICT[400]['description'], **extra_params):
        self.status_code = 400
        self.detail = detail_message + _generate_extra_params_text(**extra_params)
        super().__init__(status_code=self.status_code, detail=self.detail)


class HTTPConflict(HTTPException):
    """Raised when Conflict error occurred"""

    def __init__(self, detail_message: str = RESPONSES_DICT[409]['description'], **extra_params):
        self.status_code = 409
        self.detail = detail_message + _generate_extra_params_text(**extra_params)
        super().__init__(status_code=self.status_code, detail=self.detail)


class HTTPCustomBotIsOffline(HTTPException):
    """Raised when Conflict error occurred"""

    def __init__(self, detail_message: str = RESPONSES_DICT[406]['description'], **extra_params):
        self.status_code = 406
        self.detail = detail_message + _generate_extra_params_text(**extra_params)
        super().__init__(status_code=self.status_code, detail=self.detail)


class HTTPItemNotFound(HTTPException):
    """Raised when item not found in database"""

    def __init__(self, detail_message: str = RESPONSES_DICT[404]['description'], **extra_params):
        self.status_code = 404
        self.detail = detail_message + _generate_extra_params_text(**extra_params)
        super().__init__(status_code=self.status_code, detail=self.detail)


class HTTPProductNotFound(HTTPItemNotFound):
    def __init__(self, product_id: int | None = None, bot_id: int | None = None):
        super().__init__(detail_message="Product not found.", product_id=product_id, bot_id=bot_id)


class HTTPBotNotFound(HTTPItemNotFound):
    def __init__(self, bot_id: int | None = None):
        super().__init__(detail_message="Bot not found.", bot_id=bot_id)


class HTTPCategoryNotFound(HTTPItemNotFound):
    def __init__(self, category_id: int | None = None, bot_id: int | None = None):
        super().__init__(detail_message="Category not found.", category_id=category_id, bot_id=bot_id)


class HTTPFileNotFound(HTTPItemNotFound):
    def __init__(self, file_name: str | None = None):
        super().__init__(detail_message="File not found.", file_name=file_name)

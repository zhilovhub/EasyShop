from database.exceptions.exceptions import KwargsException


class UnknownDeepLinkArgument(KwargsException):
    """Raised if provided deep link argument is not expected"""

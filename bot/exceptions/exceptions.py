class UserNotFound(Exception):
    """Raised when provided user not found in database"""
    pass


class BotNotFound(Exception):
    """Raised when provided bot not found in database"""
    pass


class InvalidParameterFormat(Exception):
    """Raised when provided invalid data format to function"""
    pass


class InstanceAlreadyExists(Exception):
    """Raised when trying to add already existed db instance"""
    pass

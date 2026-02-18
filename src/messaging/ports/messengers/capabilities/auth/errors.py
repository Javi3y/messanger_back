class SessionPasswordNeededError(Exception):
    pass


class InvalidCodeError(Exception):
    pass


class ExpiredCodeError(Exception):
    pass


class InvalidPasswordError(Exception):
    pass

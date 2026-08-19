class ValidationError(Exception):
    ...


def check_assert(expected, value, error_msg: str):
    if value != expected:
        raise ValidationError(error_msg.replace("%value", value))

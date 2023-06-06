from functools import wraps


def set_arity(arity: int):
    """Decorated this function f with attribute arity and return.
    We need this because python won't allow us to modify the attributes of built-in function
    """

    def decorated(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.arity = arity
        return wrapper

    return decorated


# usage:
# import time
# print(set_arity(0)(time.time)())

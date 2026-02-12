from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable)


def decorator(func: F) -> F:
    """
    Functions marked with this decorator are meant to be used as decorators themselves.
    """
    return func


from .decorators import argument, command, group, option  # noqa: F401, E402

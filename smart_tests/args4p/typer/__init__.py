# This package defines Typer-style annotation based option/command declarations
from typing import Any, Callable

from ..argument import Argument as _Argument
from ..option import Option as _Option


def Option(
        *option_names: str,
        help: str = None, type: type | Callable = None, default: Any = None, required: bool = False,
        metavar: str = None, multiple: bool = False, hidden: bool = False
) -> _Option:
    '''
    :arg option_names:
        Zero or more option names.
        If no option names are given, name is generated from the parameter name (e.g. `foo_bar` -> `--foo-bar`).
    :arg help:
        Human readable description of the option, used to render the help message
    :arg type:
        Type or callable that converts the string value to the desired type.
        Defaults to the type annotation of the parameter.
    :arg default:
        Default value if the option is not provided.
    :arg required:
        Whether the option is required. Default is False.
    :arg metavar:
        User-friendly name for the option value, used in help messages.
    :arg multiple:
        Whether the option can be specified multiple times, resulting in a list of values.
        If true, the parameter type must be a list type (e.g. List[str], List[int], etc.)
    :arg hidden:
        If true, this option is hidden from help messages.
    '''

    return _Option(name=None, option_names=list(option_names), help=help, type=type,
                   default=default, required=required, metavar=metavar, multiple=multiple, hidden=hidden)


def Argument(
        type: type | Callable = str,
        multiple: bool = False,
        required: bool = True,
        metavar: str = None,
        help: str = None,
        default: Any = None
) -> _Argument:
    '''
    :arg help:
        Human readable description of the option, used to render the help message
    :arg type:
        Type or callable that converts the string value to the desired type.
        Defaults to the type annotation of the parameter.
    :arg default:
        Default value if the option is not provided.
    :arg required:
        Whether the option is required. Default is False.
    :arg metavar:
        User-friendly name for the option value, used in help messages.
    :arg multiple:
        Whether the option can be specified multiple times, resulting in a list of values.
        If true, the parameter type must be a list type (e.g. List[str], List[int], etc.)
    '''
    return _Argument(name=None, type=type, multiple=multiple, required=required, metavar=metavar, help=help, default=default)


class Exit(Exception):
    '''
    Raise this exception to exit the CLI with the given exit code
    '''
    def __init__(self, code: int):
        self.code = code

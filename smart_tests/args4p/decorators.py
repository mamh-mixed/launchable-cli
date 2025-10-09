from __future__ import annotations

from typing import Any, Callable, Optional, Type

from . import decorator
from .argument import Argument
from .command import Command, Group
from .option import Option
from .parameter import Parameter


def _command(
        name: Optional[str] = None,
        cls: Optional[Type[Command]] = Command,
):
    def decorator(f: Callable) -> Command:

        if name is not None:
            cmd_name = name
        else:
            cmd_name = f.__name__.lower().replace("_", "-")

        try:
            params = f.__args4p_params__  # type: ignore
        except AttributeError:
            # if __args4p_params__ doesn't exist that's OK
            params = []
        else:
            del f.__args4p_params__  # type: ignore
            params = reversed(params)

        return cls(name=cmd_name, callback=f, params=params)

    return decorator


@decorator
def command(name: Optional[str] = None) -> Callable[[...], Command]:
    return _command(name, Command)


@decorator
def group(name: Optional[str] = None) -> Callable[[...], Group]:
    return _command(name, Group) # type: ignore


# is_flag is replaced by type=bool
@decorator
def option(
    *param_decls: str,  # option names, followed by the variable name
    help: str = None, type: type = None, default: Any = None, required: bool = False, metavar: str = None, multiple: bool = False
) -> Callable:
    '''
    Args:
        type:

    '''
    def decorator(f: Callable) -> Callable:
        if len(param_decls) == 0:
            raise "Variable name is required"

        variable_name = param_decls[-1]
        if len(param_decls) == 1:
            option_names = [f"--{variable_name.replace('_', '-')}"]
        else:
            option_names = list(param_decls[:-1])

        o = Option(
            name=variable_name,
            option_names=option_names,
            help=help,
            type=type,
            default=default,
            required=required,
            metavar=metavar,
            multiple=multiple)

        return _attach(f, o)

    return decorator


@decorator
def argument(
    name: str,
    type: type = str,
    multiple: bool = False,
    required: bool = True,
    metavar: str = None,
    help: str = None,
) -> Callable:
    a = Argument(name=name, type=type, multiple=multiple, required=required, metavar=metavar, help=help)
    return lambda f: _attach(f, a)


def _attach(f: Callable[[...], Any], param: Parameter):
    # depending on whether a command annotation comes before/after parameter annotations, 'f' might be
    # a naked user-defined function or a Command instance
    if isinstance(f, Command):
        f.add_param(param, True)
    else:
        if not hasattr(f, "__args4p_params__"):
            f.__args4p_params__ = []  # type: ignore

        f.__args4p_params__.append(param)  # type: ignore

    return f

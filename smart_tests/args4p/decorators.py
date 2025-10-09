from __future__ import annotations

from typing import Any, Callable, Optional, Type

from .argument import Argument
from .command import Command, Group
from .option import Option


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


def command(name: Optional[str] = None) -> Callable[[...], Command]:
    return _command(name, Command)


def group(name: Optional[str] = None) -> Callable[[...], Group]:
    return _command(name, Group) # type: ignore


# is_flag is replaced by type=bool
def option(
    *param_decls: str,  # option names, followed by the variable name
    help: str = None, type: type = None, default: Any = None, required: bool = False, metavar: str = None, many: bool = False
) -> Callable:
    def decorator(f: Callable) -> Callable:
        if len(param_decls) == 0:
            raise "Variable name is required"

        variable_name = param_decls[-1]
        if len(param_decls) == 1:
            option_names = [f"--{variable_name.replace('_', '-')}"]
        else:
            option_names = param_decls[:-1]

        o = Option(
            name=variable_name,
            option_names=option_names,
            help=help,
            type=type,
            default=default,
            required=required,
            metavar=metavar,
            many=many)

        return _attach(f, o)

    return decorator


def argument(
    name: str,
    type: type = str,
    nargs: int = 1,
    required: bool = True,
    metavar: str = None,
    help: str = None,
) -> Callable:
    a = Argument(name=name, type=type, nargs=nargs, required=required, metavar=metavar, help=help)
    return lambda f: _attach(f, a)


def _attach(f: Callable[[...], Any], param: Option | Argument):
    if isinstance(f, Command):
        f.add_param(param)
    else:
        if not hasattr(f, "__args4p_params__"):
            f.__args4p_params__ = []  # type: ignore

        f.__args4p_params__.append(param)  # type: ignore

    return f

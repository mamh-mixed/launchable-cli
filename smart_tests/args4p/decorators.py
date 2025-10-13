from __future__ import annotations

import inspect
from typing import Annotated, Any, Callable, Optional, Type, get_args, get_origin

from . import decorator
from .argument import Argument
from .command import Command, Group
from .exceptions import BadConfigException
from .option import Option, NO_DEFAULT
from .parameter import Parameter


def _command(
        name: Optional[str] = None,
        help: Optional[str] = None,
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

        # pick up parameters declared in annotations
        sig = inspect.signature(f)
        for pname, param in sig.parameters.items():
            if get_origin(param.annotation) == Annotated:
                args = get_args(param.annotation)
                for a in args:
                    if isinstance(a, Parameter):
                        if a.name is None:
                            a.name = pname
                        if a.type is None:
                            a.type = a.normalize_type(args[0])
                        if isinstance(a, Option):
                            if a.option_names is None or len(a.option_names) == 0:
                                a.option_names = [f"--{a.name.replace('_', '-')}"]
                        params.append(a)

        return cls(name=cmd_name, help=help, callback=f, params=params)

    return decorator


@decorator
def command(name: Optional[str] = None, help: Optional[str] = None) -> Callable[[...], Command]:
    return _command(name, help, Command)


@decorator
def group(name: Optional[str] = None, help: Optional[str] = None) -> Callable[[...], Group]:
    return _command(name, help, Group)  # type: ignore


@decorator
def option(
        *param_decls: str,
        help: str = None, type: type | Callable = None, default: Any = NO_DEFAULT, required: bool = False,
        metavar: str = None, multiple: bool = False, hidden: bool = False
) -> Callable:
    '''
    :arg param_decls:
        Zero or more option names, followed by the variable name.
        If no option names are given, name is generated from it (e.g. `foo_bar` -> `--foo-bar`).
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

    def decorator(f: Callable) -> Callable:
        if len(param_decls) == 0:
            raise BadConfigException("Variable name is required")

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
            multiple=multiple,
            hidden=hidden)

        return _attach(f, o)

    return decorator


@decorator
def argument(
    name: str,
    type: type | Callable = str,
    multiple: bool = False,
    required: bool = True,
    metavar: str = None,
    help: str = None,
    default: Any = NO_DEFAULT
) -> Callable:
    '''
    :arg name:
        Name of the function parameter that this argument binds to.
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
    a = Argument(name=name, type=type, multiple=multiple, required=required, metavar=metavar, help=help, default=default)
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

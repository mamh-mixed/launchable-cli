import inspect
import types
from typing import Annotated, Any, Callable, Optional, Union, get_args, get_origin

from smart_tests.args4p.exceptions import BadConfigException


def to_type(p: inspect.Parameter) -> Optional[type]:
    '''
    Given output from inspect.signature, extract the type annotation.
    '''
    annotation = p.annotation
    if annotation == inspect.Parameter.empty:
        return None

    # we expect a List[something] and we want to extract 'something'

    origin = get_origin(annotation)
    if origin is Annotated:
        return get_args(annotation)[0]

    return annotation


def normalize_type(t) -> type:
    if isinstance(t, types.UnionType) or get_origin(t) is Union:
        # x|None is a common typing of a parameter that confuses args4p.
        # we want to normalize it to just x
        # Not sure when UnionType is used and when Union is used, but they both seem to appear
        args = get_args(t)
        if len(args) == 2 and args[1] is type(None):
            return args[0]

    return t


class Parameter:
    '''
    Common parts of Argument and Option
    '''

    # the name of the argument, used as the variable name in the user function
    # when created from typer.Option or typer.Argument, this is not set until attached to a command
    name: str

    multiple: bool  # True if this argument can appear multiple times
    required: bool  # True if this argument is required
    metavar: str | None  # the name to use in help messages for the argument value
    help: str | None  # the help message for this argument
    default: Any  # the default value if the argument/option is not provided
    clazz: str  # "argument" or "option"

    # convert the string argument to a value.
    # For multiple=True, this is the type of each individual value.
    # 'type' object itself, like 'int' is a convenient callable to do just that
    type: type | Callable

    def attach_to_command(self, command):  # typing command makes reference circular
        def error(msg: str):
            raise BadConfigException(
                f"{msg} in function '{command.callback.__name__}': "
                f"{inspect.getsourcefile(command.callback)}:{inspect.getsourcelines(command.callback)[1]}")

        for name, param in inspect.signature(command.callback).parameters.items():
            if name == self.name:
                # we found the parameter that matches the name
                if self.type is None:
                    def infer_type() -> type:
                        t = normalize_type(to_type(param))
                        if t is None:
                            raise error(f"Type annotation is missing on parameter '{name}'")
                        if self.multiple:
                            # we expect a List[something] and we want to extract 'something'
                            if get_origin(t) is list:
                                return get_args(t)[0]
                            raise error(f"multiple=True requires a List[T] type annotation with parameter '{name}'")
                        else:
                            return t

                    self.type = infer_type()

                return

        raise error(f"No parameter named '{self.name}' found")

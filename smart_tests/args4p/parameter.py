import inspect
from typing import Any, Callable, Annotated, Optional, get_origin, get_args

from click import Parameter

from smart_tests.args4p.exceptions import BadConfigException

def to_type(p :inspect.Parameter) -> Optional[type]:
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

class Parameter:
    '''
    Common parts of Argument and Option
    '''

    # the name of the argument, used as the variable name in the user function
    # when created from typer.Option or typer.Argument, this is not set until attached to a command
    name: str

    multiple: bool  # True if this argument can appear multiple times
    required: bool  # True if this argument is required
    metavar: str  # the name to use in help messages for the argument value
    help: str  # the help message for this argument
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
                        t = to_type(param)
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

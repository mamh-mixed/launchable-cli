import inspect
from typing import Any, Callable

from smart_tests.args4p.exceptions import BadConfigException


class Parameter:
    '''
    Common parts of Argument and Option
    '''
    name: str   # the name of the argument, used as the variable name in the user function
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
                    def infer_type(annotation) -> type:
                        if self.multiple:
                            # we expect a List[something] and we want to extract 'something'
                            if getattr(annotation, '__origin__', None) is list:
                                return annotation.__args__[0]
                            raise error(f"multiple=True requires a List[T] type annotation with parameter '{name}'")
                        else:
                            if annotation == inspect.Parameter.empty:
                                raise error(f"Type annotation is missing on parameter '{name}'")
                            return annotation

                    self.type = infer_type(param.annotation)
                return

        raise error(f"No parameter named '{self.name}' found")

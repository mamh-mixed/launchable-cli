import inspect
from typing import Any

from smart_tests.args4p.exceptions import BadConfigException


class Parameter:
    '''
    Common parts of Argument and Option
    '''
    name: str   # the name of the argument, used as the variable name in the user function
    multiple: bool  # True if this argument can appear multiple times
    type: type  # the type to convert the string argument to. For multiple=True, this is the type of each individual value
    required: bool  # True if this argument is required
    metavar: str  # the name to use in help messages for the argument value
    help: str  # the help message for this argument
    default: Any  # the default value if the argument/option is not provided

    clazz: str # "argument" or "option"

    def attach_to_command(self, parent : 'Command'):
        def error(msg: str):
            raise BadConfigException(f"{msg} in function '{parent.callback.__name__}': {inspect.getsourcefile(parent.callback)}:{inspect.getsourcelines(parent.callback)[1]}")

        for name, param in inspect.signature(parent.callback).parameters.items():
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

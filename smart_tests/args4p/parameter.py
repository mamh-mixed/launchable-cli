import inspect
from typing import Any

from smart_tests.args4p.exceptions import BadConfigException


class Parameter:
    '''
    Common parts of Argument and Option
    '''
    name: str   # the name of the argument, used as the variable name in the user function
    multiple: bool  # True if this argument can appear multiple times
    type: type  # the type to convert the string argument to
    required: bool  # True if this argument is required
    metavar: str  # the name to use in help messages for the argument value
    help: str  # the help message for this argument
    default: Any  # the default value if the argument/option is not provided

    def attach_to_command(self, parent : 'Command'):
        for name, param in inspect.signature(parent.callback).parameters.items():
            if name == self.name:
                # we found the parameter that matches the name
                if self.type is None:
                    self.type = param.annotation
                return

        raise BadConfigException(
            f"No parameter named '{self.name}' found in function '{parent.callback.__name__}': {inspect.getsourcefile(parent.callback)}:{inspect.getsourcelines(parent.callback)[1]}")

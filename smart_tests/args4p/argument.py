from typing import Any, Optional

from .exceptions import BadCmdLineException
from .option import NO_DEFAULT
from .parameter import Parameter


class Argument(Parameter):
    clazz = "argument"

    def __init__(self, name: Optional[str], type: type = str, multiple: bool = False,
                 required: bool = True, metavar: str = None, help: str = None, default: Any = NO_DEFAULT):
        self.name = name
        self.type = type
        self.multiple = multiple
        self.required = required
        self.metavar = metavar
        self.help = help
        self.default = default

    def append(self, existing: Any, arg: str):
        '''
        Given the current value 'existing' that represents the present value to invoke the user function with,
        this method is called when another argument 'arg' is consumed from the command line to create the updated
        value that replaces 'existing'.
        '''

        try:
            v = self.type(arg)
        except ValueError as e:
            raise BadCmdLineException(f"Invalid value '{arg}' for argument '{self.name}'") from e

        if self.multiple:
            if existing is None:
                existing = []
            existing.append(v)
            return existing
        else:
            return v

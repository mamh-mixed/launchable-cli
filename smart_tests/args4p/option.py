from typing import Any, Optional

from .exceptions import BadCmdLineException
from .parameter import Parameter

class NoDefault:
    '''
    If there's no default value configured for option/argument, we use `NO_DEFAULT`.
    In contrast, `None` is a valid and very typical default value.
    '''
    pass

NO_DEFAULT = NoDefault()

class Option(Parameter):
    clazz = "option"

    hidden: bool

    def __init__(self, name: Optional[str], option_names: list[str], help: str = None, type: type = str,
                 default: Any = NO_DEFAULT, required: bool = False, metavar: str = None, multiple: bool = False,
                 hidden: bool = False):
        self.name = name
        self.option_names = option_names
        self.help = help
        self.type = type
        self.default = default
        self.required = required
        self.metavar = metavar
        self.multiple = multiple
        self.hidden = hidden

    def append(self, existing: Any, option_name: str, args):  # args is ArgList, but typing it creates a circular import
        '''
        Given the current value 'existing' that represents the present value to invoke the user function with,
        this method is called when this option was specified as 'option_name' on the command line.
        'args' is pointing at the next argument after 'option_name', which may be the value for this option.
        '''

        if self.type == bool:
            v = True
        else:
            v = args.eat(option_name)
            try:
                v = self.type(v)
            except ValueError as e:
                raise BadCmdLineException(f"Invalid value '{v}' for option '{option_name}'") from e

        if self.multiple:
            if existing is None:
                existing = []
            existing.append(v)
            return existing
        else:
            return v

    def __repr__(self):
        return (f"Option(name={self.name!r}, option_names={self.option_names!r}, help={self.help!r}, "
                f"type={self.type.__name__!r}, default={self.default!r}, required={self.required!r}, "
                f"metavar={self.metavar!r}, many={self.multiple!r})")

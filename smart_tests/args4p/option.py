from typing import Any

from .parameter import Parameter


class Option(Parameter):
    def __init__(self, name: str, option_names: list[str], help: str = None, type: type = str,
                 default: Any = None, required: bool = False, metavar: str = None, multiple : bool = False):
        self.name = name
        self.option_names = option_names
        self.help = help
        self.type = type
        self.default = default
        self.required = required
        self.metavar = metavar
        self.multiple = multiple

    def append(self, existing: Any, option_name: str, args: 'ArgList'):
        '''
        Given the current value 'existing' that represents the present value to invoke the user function with,
        this method is called when this option was specified as 'option_name' on the command line.
        'args' is pointing at the next argument after 'option_name', which may be the value for this option.
        '''

        if self.type==bool:
            v = True
        else:
            v = self.type(args.eat(option_name))

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

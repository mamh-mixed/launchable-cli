from typing import Any


class Option:
    def __init__(self, variable_name: str, option_names: list[str], help: str = None, type: type = str,
                 default: Any = None, required: bool = False, metavar: str = None):
        self.variable_name = variable_name
        self.option_names = option_names
        self.help = help
        self.type = type
        self.default = default
        self.required = required
        self.metavar = metavar

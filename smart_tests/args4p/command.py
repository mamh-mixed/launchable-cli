from __future__ import annotations

import inspect
import re
from typing import Any, Callable, cast, List, Optional

from . import decorator
from .argument import Argument
from .exceptions import BadCmdLineException, BadConfigException
from .option import Option
from .parameter import Parameter


class Command:
    parent: Group = None        # if this is a sub-command of another command, this is the parent command
    options: list[Option]
    arguments: list[Argument]
    name: str
    callback: Callable

    def __init__(self, name: str, callback: Callable, params: list[Parameter]):
        self.name = name
        self.callback = callback
        self.options = []
        self.arguments = []
        for p in params:
            self.add_param(p)

    def add_param(self, param: Parameter, prepend: bool = False):
        '''
        Attach an option/argument to this command. Use this to programmatically construct Command with parameters.
        It is possible to attach the same parameter to different commands simultaneously.

        :param prepend
            when we are adding parameter from decorators, things show up in the reverse order, so we need to prepend,
            not append.
        '''
        param.attach_to_command(self)
        col = self.options if isinstance(param, Option) else self.arguments
        if prepend:
            col.insert(0, param)
        else:
            col.append(param)

    def __call__(self, *_args: str) -> Any:
        '''
        Given the command line arguments, parse them, bind them to the user function parameters,
        and invoke the function. This method returns the return value of the user function.
        '''
        self.check_consistency()

        invoker = _Invoker(self)
        args = _ArgList(list(_args))

        while args.has_more():
            a = args.eat(None)
            if a=="--":
                # everything after this is a positional argument
                while args.has_more():
                    invoker.eat_arg(args.eat(None))
            elif a.startswith("-"):
                invoker.eat_options(a, args)
            elif isinstance(invoker.command, Group):
                invoker = invoker.sub_command(a)
            else:
                invoker.eat_arg(a)

        return invoker.invoke()

    def check_consistency(self):
        """
        Validate that the command configuration is consistent and well-formed.
        Raises BadConfigException if any issues are found.
        """

        # Get function signature for parameter analysis
        sig = inspect.signature(self.callback)
        func_params = list(sig.parameters.keys())

        # For Group sub-commands, first parameter is context from parent
        # For regular commands, all parameters should be covered by decorators
        context_param_offset = 1 if self.parent is not None else 0
        expected_func_params = func_params[context_param_offset:]

        def error(msg: str) -> BadConfigException:
            return BadConfigException(
                f"{msg} in function '{self.callback.__name__}' signature: "
                f"{inspect.getsourcefile(self.callback)}:{inspect.getsourcelines(self.callback)[1]}")

        # Check for missing function parameters
        for p in self.options:
            if p.name not in func_params:
                raise error(f"@option names '{p.name}' but no such parameter exists")

        for a in self.arguments:
            if a.name not in func_params:
                raise error(f"@argument names '{a.name}' but no such parameter exists")

        # Collect all parameter names from decorators
        decorator_param_names = set()
        for p in self.options + self.arguments:
            if p.name in decorator_param_names:
                raise error(f"Duplicate parameter name '{p.name}' found in command '{self.name}' decorators")
            decorator_param_names.add(p.name)

        # Check for required parameter with default value
        for p in self.options + self.arguments:
            if p.required and p.default is not None:
                raise error(f"'{p.name}' is marked as required but with default value '{p.default}'")

        # Check for uncovered function parameters
        for p in expected_func_params:
            if p not in decorator_param_names:
                raise error(f"Function parameter '{p}' is not covered by any @option or @argument decorator")

        # Type system checks
        for p in self.options + self.arguments:
            fp = sig.parameters[p.name]

            # Check if multiple=True is used correctly with List type
            if p.multiple:
                annotation = fp.annotation
                if annotation == inspect.Parameter.empty:
                    raise error(f"Parameter '{p.name}' with multiple=True requires a type annotation")
                if not (hasattr(annotation, '__origin__') and annotation.__origin__ is list):
                    raise error(f"Parameter '{p.name}' with multiple=True requires a List[T]")

            # Check default value type compatibility
            if p.default is not None and not isinstance(p.default, p.type):
                raise error(
                    f"Default value '{p.default}' for parameter '{p.name}' is incompatible with type '{p.type.__name__}'")

        # Check for duplicate option names
        all_option_names = set()
        for p in self.options:
            for name in p.option_names:
                if name in all_option_names:
                    raise error(f"Duplicate option name '{name}' found")
                all_option_names.add(name)

        # Check option name formats
        for p in self.options:
            for opt_name in p.option_names:
                if not re.match(r'^-[a-zA-Z]$|^--[a-zA-Z][-a-zA-Z0-9]*$', opt_name):
                    raise error(f"Invalid option name '{opt_name}'")

        # Check boolean option conflicts
        for p in self.options:
            if p.type == bool:
                if p.required:
                    raise error(f"It makes no sense to require a boolean option '{p.name}'")

        # Check argument ordering (required after optional)
        found_optional = False
        for a in self.arguments:
            if not a.required:
                found_optional = True
            elif found_optional:
                raise error(f"Required argument '{a.name}' cannot appear after optional arguments")

        # Check multiple arguments placement and count
        multiple_args = [arg.name for arg in self.arguments if arg.multiple]
        if len(multiple_args) > 1:
            raise error(f"Cannot have more than one multiple=True argument, found: {multiple_args}")

        if len(multiple_args) == 1:
            # multiple=True argument must be the last argument
            if self.arguments and self.arguments[-1].name != multiple_args[0]:
                raise error(f"Argument '{multiple_args[0]}' with multiple=True must be the last argument")

        # Group-specific checks
        if isinstance(self, Group):
            # Groups should not have any arguments since first arg is subcommand name
            if self.arguments:
                raise error(f"Group command '{self.name}' cannot have arguments")

            # Check for empty groups (only if this is a Group)
            if not self.commands:
                raise error(f"Group command '{self.name}' has no subcommands defined")

            # Check subcommand name conflicts
            subcommand_names = [cmd.name for cmd in self.commands]
            if len(subcommand_names) != len(set(subcommand_names)):
                duplicates = [name for name in set(subcommand_names) if subcommand_names.count(name) > 1]
                raise error(f"Duplicate subcommand names found in group '{self.name}': {duplicates}")

            # Recursively check subcommands for Groups
            for c in self.commands:
                c.check_consistency()

    def __repr__(self):
        return f"<Command name={self.name!r} options={self.options!r} arguments={self.arguments!r}>"

class Group(Command):
    '''
    Special type of command that has sub-commands, e.g. 'git commit', 'git push', where 'git' is a group command.

    A sub-command receives the return value of its parent command as the first argument to its callback function,
    which is how we expect the parent to pass the context to the child.
    '''
    commands: List[Command]

    def __init__(self, name: str, callback: Callable, params: list[Parameter]):
        super().__init__(name, callback, params)
        self.commands = []

    def add_command(self, c: Command):
        self.commands.append(c)
        if c.parent is not None:
            raise BadConfigException(f"Command '{c.name}' is already a sub-command of '{c.parent.name}'")
        c.parent = self

    @decorator
    def command(self, name: Optional[str] = None) -> Callable[[...], Command]:
        from .decorators import _command

        def decorator(f: Callable) -> Command:
            c = _command(name, Command)(f)
            self.add_command(c)
            return c
        return decorator

    @decorator
    def group(self, name: Optional[str] = None) -> Callable[[...], Group]:
        from .decorators import _command

        def decorator(f: Callable) -> Group:
            g = _command(name, Group)(f)
            self.add_command(g)
            return g
        return decorator

    def find_subcommand(self, name: str) -> Command:
        for c in self.commands:
            if c.name == name:
                return c
        # TODO: typo look up, etc
        raise BadCmdLineException(f"Unknown command: {name}")

class _ArgList:
    '''
    This class represents a list of arguments, and provides methods to consume arguments from the front of the list
    '''
    args: list[str]

    def __init__(self, args: list[str]):
        self.args = args

    def peek(self, caller: Any) -> str:
        if len(self.args) == 0:
            raise BadCmdLineException(f"{caller} is missing an argument")
        return self.args[0]

    def eat(self, caller: Any) -> str:
        if len(self.args) == 0:
            raise BadCmdLineException(f"{caller} is missing an argument")
        return self.args.pop(0)

    def has_more(self) -> bool:
        return len(self.args) > 0


class _Invoker:
    '''
    This class builds up data needed to invoke a command
    '''
    command: Command
    parent: _Invoker = None
    kwargs: dict[str, Any]

    nargs = 0  # number of arguments consumed, used to identify the processor of the next argument

    def __init__(self, command: Command):
        self.command = command
        self.kwargs = {}

    def eat_arg(self, arg: str):
        l = self.command.arguments

        if self.nargs < len(l):
            a = l[self.nargs]
        else:
            if len(l)>0 and l[-1].multiple:
                a = l[-1]
            else:
                raise BadCmdLineException(f"Too many arguments for '{self.command.name}' command: {arg}")

        self.kwargs[a.name] = a.append(self.kwargs.get(a.name), arg)
        self.nargs += 1

    def eat_options(self, option_name :str, args: _ArgList):
        inv = self
        while inv is not None:
            for o in inv.command.options:
                if option_name in o.option_names:
                    inv.kwargs[o.name] = o.append(inv.kwargs.get(o.name), option_name, args)
                    return
            inv = inv.parent

        # TODO: typo look up, etc
        raise BadCmdLineException(f"No such option '{option_name}' for '{self.command.name}' command")

    def sub_command(self, name: str) -> _Invoker:
        c = cast(Group, self.command).find_subcommand(name)
        i = _Invoker(c)
        i.parent = self
        return i

    def invoke(self) -> Any:
        '''
        Invoke the user defined methods with the right parameter bindings from options and arguments,
        then return what the function returned
        '''

        # fill in default values
        for a in self.command.arguments:
            if a.name not in self.kwargs:
                if a.required:
                    raise BadCmdLineException(f"Missing required argument '{a.name}' for command '{self.command.name}'")
                else:
                    self.kwargs[a.name] = a.default

        for o in self.command.options:
            if o.name not in self.kwargs:
                if o.required:
                    raise BadCmdLineException(f"Missing required option '{o.option_names[0]}' for command '{self.command.name}'")
                else:
                    self.kwargs[o.name] = o.default

        if self.parent is not None:
            return self.command.callback(self.parent.invoke(), **self.kwargs)
        else:
            return self.command.callback(**self.kwargs)

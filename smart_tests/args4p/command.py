from __future__ import annotations

from typing import Any, Callable, cast, List, Optional

from . import decorator
from .argument import Argument
from .exceptions import BadCmdLineException
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

    def add_param(self, param: Parameter):
        '''
        Attach an option/argument to this command. Use this to programmatically construct Command with parameters.
        It is possible to attach the same parameter to different commands simultaneously.
        '''
        param.attach_to_command(self)
        if isinstance(param, Option):
            self.options.append(param)
        else:
            self.arguments.append(param)

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
            if a.startswith("--"):
                invoker.eat_options(a, args)
            elif isinstance(invoker.command, Group):
                invoker = invoker.sub_command(a)
            else:
                invoker.eat_arg(a)

        return invoker.invoke()

    def check_consistency(self):
        pass # TODO: make sure options & arguments are well constructed

    def __repr__(self):
        return f"<Command name={self.name!r} options={self.options!r} arguments={self.arguments!r}>"

class Group(Command):
    '''
    Special type of command that has sub-commands, e.g. 'git commit', 'git push', where 'git' is a group command.
    '''
    commands: List[Command]

    def __init__(self, name: str, callback: Callable, params: list[Parameter]):
        super().__init__(name, callback, params)
        self.commands = []

    @decorator
    def command(self, name: Optional[str] = None) -> Callable[[...], Command]:
        from .decorators import _command

        def decorator(f: Callable) -> Command:
            c = _command(name, Command)(f)
            self.commands.append(c)
            return c
        return decorator

    @decorator
    def group(self, name: Optional[str] = None) -> Callable[[...], Group]:
        from .decorators import _command

        def decorator(f: Callable) -> Group:
            g = _command(name, Group)(f)
            self.commands.append(g)
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
            r = self.parent.invoke()
            # TODO: pass 'r'

        return self.command.callback(**self.kwargs)

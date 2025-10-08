from __future__ import annotations

from typing import Any, Callable, cast

from .argument import Argument
from .exceptions import BadCmdLineException
from .group import Group
from .option import Option


class Command:
    parent: Group = None        # if this is a sub-command of another command, this is the parent command
    options: list[Option]
    arguments: list[Argument]
    name: str
    callback: Callable

    def __init__(self, name: str, callback: Callable, params: list[Option | Argument]):
        self.name = name
        self.callback = callback
        self.options = [p for p in params if isinstance(p, Option)]
        self.arguments = [p for p in params if isinstance(p, Argument)]

    def add_param(self, param: Option | Argument):
        if isinstance(param, Option):
            self.options.append(param)
        else:
            self.arguments.append(param)

    def __call__(self, *args: str):
        class Invoker:
            '''
            This class builds up data needed to invoke a command
            '''
            command: Command
            parent: Invoker = None
            kwargs: dict[str, Any] = {}

            nargs = 0  # number of arguments consumed, used to identify the processor of the next argument

            def __init__(self, command: Command):
                self.command = command
                # TODO: fill kwargs with default values

            def next_arg(self) -> Argument:
                pass  # TODO

            def eat_arg(self, arg: str):
                a = self.next_arg()
                if a is None:
                    raise BadCmdLineException(f"Too many arguments for '{self.command.name}' command")
                self.kwargs[a.name] = a.append(self.kwargs[a.name], arg)
                self.nargs += 1

            def sub_command(self, name: str) -> Invoker:
                c = cast(Group, self.command).find_subcommand(name)
                if c is None:
                    raise BadCmdLineException(f"Unknown sub-command '{name}' for '{self.command.name}' command")
                i = Invoker(c)
                i.parent = self
                return i

            def invoke(self) -> Any:
                '''
                Invoke the user defined methods with the right parameter bindings from options and arguments,
                then return what the function returned
                '''
                if self.parent is not None:
                    r = self.parent.invoke()
                    # TODO: pass 'r'
                return callable(**self.kwargs)

        invoker = Invoker(self)

        while len(args) > 0:
            a = args[0]
            if a.startswith("--"):
                pass  # TODO
            elif isinstance(invoker.command, Group):
                invoker = invoker.sub_command(a)
            else:
                invoker.eat_arg(a)

        return invoker.invoke()

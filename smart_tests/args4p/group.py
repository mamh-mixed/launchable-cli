from __future__ import annotations

from typing import Callable, List, Optional

from .command import Command
from .decorators import _command


class Group(Command):
    commands: List[Command] = []

    def command(self, name: Optional[str] = None) -> Callable[[...], Command]:
        def decorator(f: Callable) -> Command:
            c = _command(name, Command)(f)
            self.commands.append(c)
            return c
        return decorator

    def group(self, name: Optional[str] = None) -> Callable[[...], Group]:
        def decorator(f: Callable) -> Group:
            g = _command(name, Group)(f)
            self.commands.append(g)
            return g
        return decorator

    def find_subcommand(self, name: str) -> Command:
        pass  # TODO

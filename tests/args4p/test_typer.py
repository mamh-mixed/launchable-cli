from typing import Annotated
from unittest import TestCase

import smart_tests.args4p as args4p
import smart_tests.args4p.typer as typer


class TyperTest(TestCase):
    def test_invocation(self):
        @args4p.group()
        def cli(foo: Annotated[bool, typer.Option()]):
            self.assertTrue(foo)
            return "cli called"

        @cli.command()
        def cmd1(parent_output: str, bar: Annotated[int, typer.Option("--baz")] = 0):
            self.assertEqual(parent_output, "cli called")
            self.assertEqual(bar, 3)
            return "exit code"

        @cli.command()
        def cmd2():
            self.fail("Shouldn't be called")

        r = cli("cmd1", "--foo", "--baz", "3")
        self.assertEqual("exit code", r)

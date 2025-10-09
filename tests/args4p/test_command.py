from unittest import TestCase

import smart_tests.args4p as args4p


class CommandTest(TestCase):
    def test_invocation(self):
        cli_called = False
        cmd1_called = False

        @args4p.group()
        @args4p.option("--foo", "foo")
        def cli(foo :bool):
            nonlocal cli_called
            cli_called = True
            self.assertTrue(foo)

        @cli.command()
        @args4p.option("--bar", "bar")
        def cmd1(bar :int):
            nonlocal cmd1_called
            cmd1_called = True
            self.assertEqual(bar,3)
            return "exit code"

        @cli.command()
        def cmd2():
            self.fail("Shouldn't be called")

        r = cli("cmd1","--foo","--bar","3")
        self.assertEqual("exit code", r)

        self.assertTrue(cli_called)
        self.assertTrue(cmd1_called)

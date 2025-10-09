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

    def test_option_default_value(self):
            v = None

            @args4p.command()
            @args4p.option("--foo", "foo", default=3)
            def cli(foo: int):
                nonlocal v
                v = foo

            cli()
            self.assertEqual(v,3)

            cli("--foo","5")
            self.assertEqual(v,5)


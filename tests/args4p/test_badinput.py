from unittest import TestCase

import smart_tests.args4p as args4p
from smart_tests.args4p.exceptions import BadCmdLineException


class BadInputTest(TestCase):
    """Test suite for bad values given by users, which we want to handle very well"""

    # 1. Missing Required Parameters

    def test_missing_required_argument(self):
        """Test that missing required argument produces helpful error message"""
        @args4p.command()
        @args4p.argument("name")
        def cmd(name: str):
            pass

        with self.assertRaises(BadCmdLineException) as e:
            cmd()

        self.assertIn("Missing required argument", str(e.exception))
        self.assertIn("'name'", str(e.exception))
        self.assertIn("command 'cmd'", str(e.exception))

    def test_missing_required_option(self):
        """Test that missing required option produces helpful error message"""
        @args4p.command()
        @args4p.option("--config", "config", required=True)
        def cmd(config: str):
            pass

        with self.assertRaises(BadCmdLineException) as e:
            cmd()

        self.assertIn("Missing required option", str(e.exception))
        self.assertIn("--config", str(e.exception))
        self.assertIn("command 'cmd'", str(e.exception))

    def test_missing_multiple_required_arguments(self):
        """Test error message when first of multiple required arguments is missing"""
        @args4p.command()
        @args4p.argument("source")
        @args4p.argument("dest")
        def cmd(source: str, dest: str):
            pass

        with self.assertRaises(BadCmdLineException) as e:
            cmd()

        # Should complain about the first missing argument
        self.assertIn("Missing required argument", str(e.exception))
        self.assertIn("'source'", str(e.exception))

    def test_missing_second_required_argument(self):
        """Test error message when second of multiple required arguments is missing"""
        @args4p.command()
        @args4p.argument("source")
        @args4p.argument("dest")
        def cmd(source: str, dest: str):
            pass

        with self.assertRaises(BadCmdLineException) as e:
            cmd("file1.txt")  # Only provided first argument

        # Should complain about the second missing argument
        self.assertIn("Missing required argument", str(e.exception))
        self.assertIn("'dest'", str(e.exception))

    # 2. Too Many Arguments

    def test_too_many_arguments_single(self):
        """Test error when providing too many arguments to command expecting one"""
        @args4p.command()
        @args4p.argument("name")
        def cmd(name: str):
            pass

        with self.assertRaises(BadCmdLineException) as e:
            cmd("arg1", "arg2")

        self.assertIn("Too many arguments", str(e.exception))
        self.assertIn("'cmd'", str(e.exception))
        self.assertIn("arg2", str(e.exception))

    # 3. Unknown/Typo Options

    def test_unknown_option_long(self):
        """Test error message for unknown long option"""
        @args4p.command()
        @args4p.option("--known", "known")
        def cmd(known: str = ""):
            pass

        with self.assertRaises(BadCmdLineException) as e:
            cmd("--unknown")

        self.assertIn("No such option", str(e.exception))
        self.assertIn("--unknown", str(e.exception))
        self.assertIn("'cmd'", str(e.exception))

    def test_unknown_option_short(self):
        """Test error message for unknown short option"""
        @args4p.command()
        @args4p.option("-v", "--verbose", "verbose", type=bool)
        def cmd(verbose: bool):
            pass

        with self.assertRaises(BadCmdLineException) as e:
            cmd("-x")

        self.assertIn("No such option", str(e.exception))
        self.assertIn("-x", str(e.exception))

    def test_typo_in_option_with_suggestion(self):
        """Test typo suggestion picks the closest match among multiple options"""
        @args4p.command()
        @args4p.option("--verbose", "verbose", type=bool)
        @args4p.option("--debug", "debug", type=bool)
        @args4p.option("--verify", "verify", type=bool)
        def cmd(verbose: bool, debug: bool, verify: bool):
            pass

        with self.assertRaises(BadCmdLineException) as e:
            cmd("--vebose")  # Closer to "verbose" than others

        self.assertIn("did you mean", str(e.exception))
        self.assertIn("--verbose", str(e.exception))

    def test_unknown_option_no_suggestion_too_different(self):
        """Test that very different option names don't produce suggestions"""
        @args4p.command()
        @args4p.option("--verbose", "verbose", type=bool)
        def cmd(verbose: bool):
            pass

        with self.assertRaises(BadCmdLineException) as e:
            cmd("--completely-different")

        self.assertIn("No such option", str(e.exception))
        # Should not suggest anything because it's too different
        self.assertNotIn("--verbose", str(e.exception))

    # 4. Unknown/Typo Subcommands (for Groups)

    def test_unknown_subcommand(self):
        """Test error message for unknown subcommand"""
        @args4p.group()
        def cli():
            pass

        @cli.command()
        def known(context):
            pass

        with self.assertRaises(BadCmdLineException) as e:
            cli("unknown")

        self.assertIn("Unknown command", str(e.exception))
        self.assertIn("unknown", str(e.exception))

    def test_typo_in_subcommand_with_suggestion(self):
        """Test that typos in subcommand names provide helpful suggestions"""
        @args4p.group()
        def cli():
            pass

        @cli.command()
        def commit(context):
            pass

        @cli.command()
        def push(context):
            pass

        with self.assertRaises(BadCmdLineException) as e:
            cli("comit")  # Missing 'm'

        self.assertIn("Unknown command", str(e.exception))
        self.assertIn("comit", str(e.exception))
        self.assertIn("did you mean", str(e.exception))
        self.assertIn("commit", str(e.exception))

    def test_missing_subcommand(self):
        """Test error message when group is invoked without subcommand"""
        from smart_tests.args4p.typer import Exit

        @args4p.group()
        def cli():
            pass

        @cli.command()
        def sub(context):
            pass

        # When group is called without subcommand, it prints help and exits
        with self.assertRaises(Exit) as e:
            cli()

        self.assertEqual(e.exception.code, 1)

    # 5. Invalid Type Conversions

    def test_invalid_integer_option(self):
        """Test error message when option expects int but gets non-numeric string"""
        @args4p.command()
        @args4p.option("--count", "count", type=int)
        def cmd(count: int = 0):
            pass

        with self.assertRaises(BadCmdLineException) as e:
            cmd("--count", "abc")

        self.assertIn("Invalid value", str(e.exception))
        self.assertIn("abc", str(e.exception))
        self.assertIn("--count", str(e.exception))

    def test_invalid_integer_argument(self):
        """Test error message when argument expects int but gets non-numeric string"""
        @args4p.command()
        @args4p.argument("count", type=int)
        def cmd(count: int):
            pass

        with self.assertRaises(BadCmdLineException) as e:
            cmd("notanumber")

        self.assertIn("Invalid value", str(e.exception))
        self.assertIn("notanumber", str(e.exception))
        self.assertIn("'count'", str(e.exception))

    def test_invalid_float_option(self):
        """Test error message when option expects float but gets invalid string"""
        @args4p.command()
        @args4p.option("--ratio", "ratio", type=float)
        def cmd(ratio: float = 0):
            pass

        with self.assertRaises(BadCmdLineException) as e:
            cmd("--ratio", "not-a-float")

        self.assertIn("Invalid value", str(e.exception))
        self.assertIn("not-a-float", str(e.exception))
        self.assertIn("--ratio", str(e.exception))

    def test_invalid_custom_type_converter(self):
        """Test error message when custom type converter raises ValueError"""
        def positive_int(value: str) -> int:
            i = int(value)
            if i <= 0:
                raise ValueError("must be positive")
            return i

        @args4p.command()
        @args4p.option("--count", "count", type=positive_int)
        def cmd(count: int = 0):
            pass

        with self.assertRaises(BadCmdLineException) as e:
            cmd("--count", "-5")

        self.assertIn("Invalid value", str(e.exception))
        self.assertIn("-5", str(e.exception))
        self.assertIn("must be positive", str(e.exception))
        self.assertIn("--count", str(e.exception))

    # 6. Missing Option Values

    def test_option_missing_value(self):
        """Test error when option expects a value but none is provided"""
        @args4p.command()
        @args4p.option("--config", "config")
        def cmd(config: str = ""):
            pass

        with self.assertRaises(BadCmdLineException) as e:
            cmd("--config")  # No value after --config

        self.assertIn("--config", str(e.exception))
        self.assertIn("missing an argument", str(e.exception))

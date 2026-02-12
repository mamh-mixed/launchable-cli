from unittest import TestCase

import smart_tests.args4p as args4p
from smart_tests.args4p.command import Command, Group
from smart_tests.args4p.exceptions import BadCmdLineException


class DecoratorTest(TestCase):
    def test_command_decorator_basic(self):
        """Test basic @command decorator"""
        @args4p.command()
        def test_cmd():
            pass

        self.assertIsInstance(test_cmd, Command)
        self.assertEqual(test_cmd.name, "test-cmd")  # underscores become dashes

    def test_command_decorator_with_name(self):
        """Test @command decorator with explicit name"""
        @args4p.command("custom-name")
        def some_function():
            pass

        self.assertEqual(some_function.name, "custom-name")

    def test_group_decorator_basic(self):
        """Test basic @group decorator"""
        @args4p.group()
        def test_group():
            pass

        self.assertIsInstance(test_group, Group)
        self.assertEqual(test_group.name, "test-group")

    def test_option_decorator_basic(self):
        """Test basic @option decorator"""
        @args4p.command()
        @args4p.option("--verbose", "verbose")
        def cmd_with_opt(verbose: str = ""):
            return f"verbose: {verbose}"

        # Option should be attached to command
        self.assertEqual(len(cmd_with_opt.options), 1)
        opt = cmd_with_opt.options[0]
        self.assertEqual(opt.name, "verbose")
        self.assertEqual(opt.option_names, ["--verbose"])

        # Test execution
        self.assertEqual(cmd_with_opt("--verbose", "yes"), "verbose: yes")

    def test_option_decorator_multiple_names(self):
        """Test @option decorator with multiple option names"""
        @args4p.command()
        @args4p.option("-v", "--verbose", "verbose")
        def f(verbose: str = ""):
            return f"verbose: {verbose}"

        opt = f.options[0]
        self.assertEqual(opt.name, "verbose")
        self.assertEqual(opt.option_names, ["-v", "--verbose"])

        # Test both forms work
        self.assertEqual(f("-v", "short"), "verbose: short")

        self.assertEqual(f("--verbose", "long"), "verbose: long")

    def test_option_decorator_inferred_name(self):
        """Test @option decorator with only variable name (inferred option name)"""
        @args4p.command()
        @args4p.option("verbose")
        def cmd_inferred(verbose: str):
            return f"verbose: {verbose}"

        opt = cmd_inferred.options[0]
        self.assertEqual(opt.name, "verbose")
        self.assertEqual(opt.option_names, ["--verbose"])

    def test_option_decorator_with_type(self):
        """Test @option decorator with type specification"""
        @args4p.command()
        @args4p.option("--count", "count", type=int, default=0)
        def f(count: int):
            return count * 2

        opt = f.options[0]
        self.assertEqual(opt.type, int)

        self.assertEqual(f("--count", "5"), 10)

    def test_option_decorator_with_default(self):
        """Test @option decorator with default value"""
        @args4p.command()
        @args4p.option("--name", "name", default="world")
        def f(name: str):
            return f"Hello {name}"

        opt = f.options[0]
        self.assertEqual(opt.default, "world")

        # Test with default
        self.assertEqual(f(), "Hello world")

        # Test with provided value
        self.assertEqual(f("--name", "Alice"), "Hello Alice")

    def test_option_decorator_boolean_flag(self):
        """Test @option decorator for boolean flags"""
        @args4p.command()
        @args4p.option("--debug", "debug", type=bool)
        def f(debug: bool):
            return f"debug: {debug}"

        opt = f.options[0]
        self.assertEqual(opt.type, bool)

        # Test flag present
        self.assertEqual(f("--debug"), "debug: True")

        # Test flag absent
        self.assertEqual(f(), "debug: False")

    def test_argument_decorator_basic(self):
        """Test basic @argument decorator"""
        @args4p.command()
        @args4p.argument("name")
        def f(name: str):
            return f"Hello {name}"

        self.assertEqual(len(f.arguments), 1)
        arg = f.arguments[0]
        self.assertEqual(arg.name, "name")
        self.assertEqual(arg.type, str)
        self.assertTrue(arg.required)

        self.assertEqual(f("Alice"), "Hello Alice")

        with self.assertRaises(BadCmdLineException) as e:
            f()
        self.assertIn("Missing required argument 'name' for command 'f'", str(e.exception))

    def test_argument_decorator_with_type(self):
        """Test @argument decorator with type specification"""
        @args4p.command()
        @args4p.argument("count", type=int)
        def f(count: int):
            return count * 3

        arg = f.arguments[0]
        self.assertEqual(arg.type, int)

        self.assertEqual(f("7"), 21)

    def test_argument_decorator_multiple_values(self):
        """Test @argument decorator with multiple values"""
        @args4p.command()
        @args4p.argument("files", multiple=True)
        def f(files: list[str]):
            return f"Processing {len(files)} files: {', '.join(files)}"

        arg = f.arguments[0]
        self.assertTrue(arg.multiple)

        self.assertEqual(f("file1.txt", "file2.txt", "file3.txt"),
                         "Processing 3 files: file1.txt, file2.txt, file3.txt")

    def test_multiple_decorators_stacking(self):
        """Test stacking multiple option and argument decorators"""
        @args4p.command()
        @args4p.option("--verbose", "verbose", type=bool)
        @args4p.option("--output", "output", default="stdout")
        @args4p.argument("input_file")
        @args4p.argument("extra_args", multiple=True, required=False)
        def complex_cmd(verbose: bool, output: str,
                        input_file: str, extra_args: list[str] = []):
            result = f"Processing {input_file}"
            if verbose:
                result += f" with output to {output}"
            if extra_args:
                result += f" with extras: {', '.join(extra_args)}"
            return result

        # Check decorators were applied
        self.assertEqual(len(complex_cmd.options), 2)
        self.assertEqual(len(complex_cmd.arguments), 2)

        # Test execution
        result = complex_cmd("input.txt", "extra1", "extra2", "--verbose", "--output", "file.out")
        self.assertEqual(result, "Processing input.txt with output to file.out with extras: extra1, extra2")

    def test_decorator_on_group_methods(self):
        """Test decorators work correctly with group command/group methods"""
        @args4p.group()
        @args4p.option("--global-opt", "global_opt")
        def main_group(global_opt: str):
            return f"global: {global_opt}"

        @main_group.command()
        @args4p.option("--local-opt", "local_opt")
        def sub_cmd(context, local_opt: str):
            return f"local: {local_opt}"

        @main_group.group()
        def sub_group(context):
            return "sub group"

        # Check structure
        self.assertEqual(len(main_group.commands), 2)
        self.assertIsInstance(main_group.commands[0], Command)
        self.assertIsInstance(main_group.commands[1], Group)

        # Check options
        self.assertEqual(len(main_group.options), 1)
        self.assertEqual(len(main_group.commands[0].options), 1)

    def test_decorator_order_matters1(self):
        """Test that decorator order affects parameter order"""
        @args4p.command()
        @args4p.argument("first")
        @args4p.argument("second", type=int)
        def f1(second: int, first: str):
            return f"{first}:{second}"
        self._assert_argument_order(f1)

    def test_decorator_order_matters2(self):
        """Test that decorator order affects parameter order"""
        @args4p.argument("first")
        @args4p.command()
        @args4p.argument("second", type=int)
        def f2(second: int, first: str):
            return f"{first}:{second}"
        self._assert_argument_order(f2)

    def test_decorator_order_matters3(self):
        """Test that decorator order affects parameter order"""
        @args4p.command()
        @args4p.argument("first")
        @args4p.argument("second", type=int)
        def f3(second: int, first: str):
            return f"{first}:{second}"
        self._assert_argument_order(f3)

    def _assert_argument_order(self, f: Command):
        # Arguments should be processed in the natural order
        self.assertEqual(len(f.arguments), 2)
        self.assertEqual(f.arguments[0].name, "first")
        self.assertEqual(f.arguments[1].name, "second")

        self.assertEqual(f("hello", "42"), "hello:42")

    def test_option_with_all_parameters(self):
        """Test option decorator with all possible parameters"""
        @args4p.command()
        @args4p.option(
            "-c", "--count", "count",
            help="Number of items",
            type=int,
            default=1,
            required=False,
            metavar="N",
            multiple=False
        )
        def full_option_cmd(count: int):
            return f"count: {count}"

        opt = full_option_cmd.options[0]
        self.assertEqual(opt.name, "count")
        self.assertEqual(opt.option_names, ["-c", "--count"])
        self.assertEqual(opt.help, "Number of items")
        self.assertEqual(opt.type, int)
        self.assertEqual(opt.default, 1)
        self.assertFalse(opt.required)
        self.assertEqual(opt.metavar, "N")
        self.assertFalse(opt.multiple)

    def test_argument_with_all_parameters(self):
        """Test argument decorator with all possible parameters"""
        @args4p.command()
        @args4p.argument(
            "files",
            type=str,
            multiple=True,
            required=True,
            metavar="FILE",
            help="Input files to process"
        )
        def full_arg_cmd(files: list):
            return f"files: {files}"

        arg = full_arg_cmd.arguments[0]
        self.assertEqual(arg.name, "files")
        self.assertEqual(arg.type, str)
        self.assertTrue(arg.multiple)
        self.assertTrue(arg.required)
        self.assertEqual(arg.metavar, "FILE")
        self.assertEqual(arg.help, "Input files to process")

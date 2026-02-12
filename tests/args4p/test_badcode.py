from typing import List
from unittest import TestCase

import smart_tests.args4p as args4p
from smart_tests.args4p.exceptions import BadConfigException


class ConsistencyCheckTest(TestCase):
    """Test suite for bad usage of args4p by a programmer"""

    # Parameter Binding Issues

    def test_missing_function_parameter_option(self):
        """Test that options referencing non-existent function parameters are caught"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.command()
            @args4p.option("--test", "nonexistent_param")
            def cmd(existing_param: str):
                pass

            cmd()

        self.assertIn("No parameter named 'nonexistent_param' found", str(e.exception))

    def test_missing_function_parameter_argument(self):
        """Test that arguments referencing non-existent function parameters are caught"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.command()
            @args4p.argument("nonexistent_param")
            def cmd(existing_param: str):
                pass

            cmd()

        self.assertIn("No parameter named 'nonexistent_param' found", str(e.exception))

    def test_uncovered_function_parameter(self):
        """Test that function parameters not covered by decorators are caught"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.command()
            @args4p.option("--covered", "covered")
            def cmd(covered: str, uncovered: str):
                pass

            cmd()

        self.assertIn("Function parameter 'uncovered'", str(e.exception))
        self.assertIn("not covered by any @option or @argument decorator", str(e.exception))

    def test_parameter_name_conflicts(self):
        """Test that duplicate parameter names across decorators are caught"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.command()
            @args4p.option("--test", "duplicate_name")
            @args4p.argument("duplicate_name")
            def cmd(duplicate_name: str):
                pass

            cmd()

        self.assertIn("Duplicate parameter name 'duplicate_name' found", str(e.exception))

    # Type System Issues

    def test_multiple_without_list_annotation(self):
        """Test that multiple=True without List annotation is caught"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.command()
            @args4p.option("--items", "items", multiple=True)
            def cmd(items: str):  # Should be List[str]
                pass

            cmd()

        self.assertIn("multiple=True requires a List[T] type annotation", str(e.exception))

    def test_multiple_without_annotation(self):
        """Test that multiple=True without any annotation is caught"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.command()
            @args4p.option("--items", "items", multiple=True)
            def cmd(items):  # No annotation
                pass

            cmd()

        self.assertIn("Type annotation is missing on parameter 'items' in function 'cmd'", str(e.exception))

    def test_default_value_type_mismatch(self):
        """Test that incompatible default values are caught"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.command()
            @args4p.option("--count", "count", type=int, default="not_a_number")
            def cmd(count: int):
                pass

            cmd()

        self.assertIn("Default value 'not_a_number'", str(e.exception))
        self.assertIn("incompatible with type 'int'", str(e.exception))

    def test_type_mismatch(self):
        """Test that incompatible default values are caught"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.command()
            @args4p.option("-p", "paths")
            def cmd(paths: List[str] = []):
                pass

            cmd()

        self.assertIn("missing multiple=True", str(e.exception))

    # Option/Argument Configuration Issues

    def test_duplicate_option_names(self):
        """Test that duplicate option names are caught"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.command()
            @args4p.option("--verbose", "verbose1")
            @args4p.option("--verbose", "verbose2")
            def cmd(verbose1: bool, verbose2: bool):
                pass

            cmd()

        self.assertIn("Duplicate option name", str(e.exception))
        self.assertIn("--verbose", str(e.exception))

    def test_invalid_option_name_format(self):
        """Test that invalid option name formats are caught"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.command()
            @args4p.option("invalid_option_name", "param", default="hello")
            def cmd(param: str):
                pass

            cmd()

        self.assertIn("Invalid option name 'invalid_option_name'", str(e.exception))

    def test_boolean_option_required_conflict(self):
        """Test that boolean options cannot be required"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.command()
            @args4p.option("--debug", "debug", type=bool, required=True)
            def cmd(debug: bool):
                pass

            cmd()

        self.assertIn("no sense to require a boolean option", str(e.exception))

    def test_required_with_default_conflict(self):
        """Test that required=True with default values is caught"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.command()
            @args4p.option("--name", "name", required=True, default="test")
            def cmd(name: str):
                pass

            cmd()

        self.assertIn("'name' is marked as required but with default value", str(e.exception))

    def test_optional_without_default_value(self):
        """Test that optional (non-required) parameters must have a default value"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.command()
            @args4p.option("--name", "name")
            def cmd(name: str):  # No default value for an option, either in signature nor the option declaration
                pass

            cmd()

        # This should fail because 'name' is optional but has no default value
        self.assertIn("Parameter 'name'", str(e.exception))

    # Argument Ordering Issues

    def test_required_argument_after_optional(self):
        """Test that required arguments cannot come after optional ones"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.command()
            @args4p.argument("optional_arg", required=False, default="default")
            @args4p.argument("required_arg")
            def cmd(optional_arg: str, required_arg: str):
                pass

            cmd()

        self.assertIn("Required argument 'required_arg' cannot appear after optional arguments", str(e.exception))

    def test_multiple_multiple_arguments(self):
        """Test that only one multiple=True argument is allowed"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.command()
            @args4p.argument("files1", multiple=True)
            @args4p.argument("files2", multiple=True)
            def cmd(files1: List[str], files2: List[str]):
                pass

            cmd()

        self.assertIn("Cannot have more than one multiple=True argument", str(e.exception))
        self.assertIn("files1", str(e.exception))
        self.assertIn("files2", str(e.exception))

    def test_multiple_argument_not_last(self):
        """Test that multiple=True arguments must be last"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.command()
            @args4p.argument("files", multiple=True)
            @args4p.argument("output")
            def cmd(files: List[str], output: str):
                pass

            cmd()

        self.assertIn("Argument 'files' with multiple=True must be the last argument", str(e.exception))

    # Group-Specific Issues

    def test_empty_group(self):
        """Test that empty groups are caught"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.group()
            def empty_group():
                pass

            empty_group()

        self.assertIn("Group command 'empty-group' has no subcommands defined", str(e.exception))

    def test_subcommand_name_conflicts(self):
        """Test that duplicate subcommand names are caught"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.group()
            def main_group():
                pass

            @main_group.command("duplicate")
            def sub1(context):
                pass

            @main_group.command("duplicate")
            def sub2(context):
                pass

            main_group()

        self.assertIn("Duplicate subcommand names found", str(e.exception))
        self.assertIn("duplicate", str(e.exception))

    def test_consistency_check_recursion(self):
        """Test that consistency checks are applied recursively to subcommands"""
        with self.assertRaises(BadConfigException) as e:
            @args4p.group()
            def main_group():
                pass

            @main_group.command()
            @args4p.option("--bad", "nonexistent")  # This should be caught in subcommand
            def bad_sub(context, existing: str):
                pass

            main_group("bad-sub")  # Should catch the error in subcommand

        self.assertIn("No parameter named 'nonexistent' found in function 'bad_sub'", str(e.exception))

from typing import List
from unittest import TestCase

import smart_tests.args4p as args4p


class HelpGenerationTest(TestCase):
    """Test suite for help/usage generation functionality"""

    def test_basic_command_help(self):
        """Test help generation for a basic command with no options or arguments"""
        @args4p.command()
        def simple_cmd():
            """A simple command that does nothing."""
            pass

        help_text = simple_cmd.format_help(program_name='hello')
        self.assertIn("Usage: hello", help_text)
        self.assertIn("A simple command that does nothing.", help_text)

    def test_complex_command_help_integration(self):
        """Test help generation for a complex command with all features"""
        @args4p.command("complex-tool")
        @args4p.option("-v", "--verbose", "verbose", type=bool, help="Enable verbose output")
        @args4p.option("--config", "config", help="Configuration file", metavar="FILE", required=True)
        @args4p.option("--retries", "retries", type=int, default=3, help="Number of retries")
        @args4p.option("--tags", "tags", multiple=True, help="Tags to apply")
        @args4p.argument("action", help="Action to perform")
        @args4p.argument("targets", multiple=True, help="Target files or directories", required=False, default=[])
        def complex_command(verbose: bool, config: str, retries: int, tags: List[str], action: str, targets: List[str]):
            """
            A complex tool for processing files and directories.

            This tool can perform various actions on files with
            configurable options and multiple targets.
            """
            pass

        help_text = complex_command.format_help(program_name='hello')
        # print(help_text)

        # Verify all sections are present and correctly formatted
        lines = help_text.split('\n')

        # Usage line
        usage_line = next(line for line in lines if line.startswith("Usage:"))
        self.assertIn("hello [OPTIONS] <ACTION> [TARGETS...]", usage_line)

        # Description
        self.assertIn("A complex tool for processing files", help_text)

        # Arguments
        self.assertIn("Arguments:", help_text)
        self.assertIn("ACTION", help_text)
        self.assertIn("Action to perform", help_text)
        self.assertIn("TARGETS [default: []] (multiple)", help_text)

        # Options
        self.assertIn("Options:", help_text)
        self.assertIn("-v, --verbose", help_text)
        self.assertIn("--config FILE", help_text)
        self.assertIn("[required]", help_text)
        self.assertIn("--retries INT", help_text)
        self.assertIn("[default: 3]", help_text)
        self.assertIn("--tags STR", help_text)
        self.assertIn("(multiple)", help_text)

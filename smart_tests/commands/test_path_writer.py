from os.path import join
from typing import Callable, List

import click

from ..app import Application
from ..testpath import TestPath


class TestPathWriter(object):
    base_path: str | None = None
    base_path_explicitly_set: bool = False  # Track if base_path was explicitly provided

    # string to write between different test paths
    separator: str = "\n"

    # pluggable logic to convert TestPath to a printable form
    formatter: Callable[[TestPath], str]

    def __init__(self, app: Application):
        self.formatter = self.default_formatter
        self._same_bin_formatter: Callable[[str], TestPath] | None = None
        self.separator = "\n"
        self.app = app

    def default_formatter(self, x: TestPath):
        """default formatter that's in line with to_test_path(str)"""
        file_name = x[0]['name']
        # Only prepend base_path if it was explicitly set via --base option
        # Auto-inferred base paths should not affect output formatting
        if self.base_path and self.base_path_explicitly_set:
            # default behavior consistent with default_path_builder's relative
            # path handling
            file_name = join(str(self.base_path), file_name)
        return file_name

    def write_file(self, file: str, test_paths: List[TestPath]):
        open(file, "w+", encoding="utf-8").write(
            self.separator.join(self.formatter(t) for t in test_paths))

    def print(self, test_paths: List[TestPath]):
        click.echo(self.separator.join(self.formatter(t)
                                       for t in test_paths))

    @property
    def same_bin_formatter(self) -> Callable[[str], TestPath] | None:
        return self._same_bin_formatter

    @same_bin_formatter.setter
    def same_bin_formatter(self, v: Callable[[str], TestPath]):
        self._same_bin_formatter = v

"""Utility type for --input-snapshot-id option."""

import click

from smart_tests.args4p import typer


class InputSnapshotId:
    """Parses either a numeric snapshot ID or @path reference."""

    def __init__(self, raw: str):
        value = str(raw)
        if value.startswith('@'):
            file_path = value[1:]
            try:
                with open(file_path, 'r', encoding='utf-8') as fp:
                    value = fp.read().strip()
            except OSError as exc:
                raise click.BadParameter(
                    f"Failed to read input snapshot ID file '{file_path}': {exc}"
                )

        try:
            parsed = int(value)
        except ValueError:
            raise click.BadParameter(
                f"Invalid input snapshot ID '{value}'. Expected a positive integer."
            )

        if parsed < 1:
            raise click.BadParameter(
                "Invalid input snapshot ID. Expected a positive integer."
            )

        self.value = parsed

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return str(self.value)

    @staticmethod
    def as_option():
        return typer.Option(
            "--input-snapshot-id",
            help="Reuse reorder results from an existing input snapshot ID or specify @path/to/file to load it",
            metavar="ID|@FILE",
            type=InputSnapshotId,
        )

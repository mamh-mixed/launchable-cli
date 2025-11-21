from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, List, Optional, Sequence, Tuple, Union

import click
from tabulate import tabulate

import smart_tests.args4p.typer as typer
from smart_tests import args4p
from smart_tests.app import Application
from smart_tests.args4p.converters import path


@dataclass(frozen=True)
class SubsetResultBase:
    order: int
    name: str


class SubsetResults:
    def __init__(self, results: Sequence[SubsetResultBase]):
        self._results: List[SubsetResultBase] = list(results)
        self._index_map = {r.name: r.order for r in self._results}

    @property
    def results(self) -> List[SubsetResultBase]:
        return self._results

    def get_order(self, name: str) -> Optional[int]:
        return self._index_map.get(name)

    @classmethod
    def from_file(cls, file_path: Path) -> "SubsetResults":
        with open(file_path, "r", encoding="utf-8") as subset_file:
            results = subset_file.read().splitlines()
        entries = [SubsetResultBase(order=order, name=result) for order, result in enumerate(results, start=1)]
        return cls(entries)


@args4p.command()
def subsets(
    app: Application,
    file_before: Annotated[Path, typer.Argument(type=path(exists=True), help="First subset file to compare")],
    file_after: Annotated[Path, typer.Argument(type=path(exists=True), help="Second subset file to compare")]
):
    """
    Compare two subset files and display changes in test order positions
    """

    before_subset = SubsetResults.from_file(file_before)
    after_subset = SubsetResults.from_file(file_after)

    # List of tuples representing test order changes (before, after, diff, test)
    rows: List[Tuple[Union[int, str], Union[int, str], Union[int, str], str]] = []

    # Calculate order difference and add each test in file_after to changes
    for result in after_subset.results:
        test_name = result.name
        after_order = result.order
        before_order = before_subset.get_order(test_name)
        if before_order is not None:
            diff = after_order - before_order
            rows.append((before_order, after_order, diff, test_name))
        else:
            rows.append(('-', after_order, 'NEW', test_name))

    # Add all deleted tests to changes
    for result in before_subset.results:
        test_name = result.name
        before_order = result.order
        if after_subset.get_order(test_name) is None:
            rows.append((before_order, '-', 'DELETED', test_name))

    # Sort changes by the order diff
    rows.sort(key=lambda x: (0 if isinstance(x[2], str) else 1, x[2]))

    # Display results in a tabular format
    headers = ["Before", "After", "After - Before", "Test"]
    tabular_data = [
        (before, after, f"{diff:+}" if isinstance(diff, int) else diff, test)
        for before, after, diff, test in rows
    ]
    click.echo_via_pager(tabulate(tabular_data, headers=headers, tablefmt="github"))

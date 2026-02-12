from typing import Annotated, List

from junitparser import TestCase, TestSuite  # type: ignore

import smart_tests.args4p.typer as typer
from smart_tests.testpath import TestPath

from ..args4p.exceptions import BadCmdLineException
from ..commands.record.tests import RecordTests
from ..commands.subset import Subset
from . import smart_tests


def path_builder(case: TestCase, suite: TestSuite, report_file: str) -> TestPath:
    test_path = []
    if suite.name:
        test_path.append({"type": "file", "name": suite.name})

    if case.classname:
        test_path.append({"type": "class", "name": case.classname})

    if case.name:
        test_path.append({"type": "testcase", "name": case.name})

    return test_path


@smart_tests.record.tests
def record_tests(
    client: RecordTests,
    reports: Annotated[List[str], typer.Argument(
        multiple=True,
        help="Test report files to process"
    )],
):
    for r in reports:
        client.report(r)

    client.path_builder = path_builder
    client.run()


@smart_tests.subset
def subset(client: Subset):
    if client.base_path is None:
        raise BadCmdLineException("Please specify base path")

    for line in client.stdin():
        if len(line.strip()) and not line.startswith(">"):
            client.test_path(line.rstrip("\n"))

    client.run()

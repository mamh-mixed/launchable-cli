from typing import Annotated, List, cast
from xml.etree import ElementTree as ET

import smart_tests.args4p.typer as typer

from ..commands.record.tests import RecordTests
from ..commands.subset import Subset
from . import smart_tests


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

    def parse_func(p: str) -> ET.ElementTree:
        tree = cast(ET.ElementTree, ET.parse(p))
        for suites in tree.iter("testsuites"):
            if len(suites) == 0:
                continue
            root_suite = suites.find('./testsuite[@name="Root Suite"]')
            if root_suite is not None:
                filepath = root_suite.get("file")
                if filepath is not None:
                    for suite in suites:
                        suite.attrib.update({"filepath": filepath})
        return tree

    client.junitxml_parse_func = parse_func
    client.run()


@smart_tests.subset
def subset(client: Subset):
    # read lines as test file names
    for t in client.stdin():
        client.test_path(t.rstrip("\n"))

    client.separator = ','
    client.run()

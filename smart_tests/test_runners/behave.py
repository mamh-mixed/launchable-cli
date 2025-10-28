import os
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
        for suite in tree.iter("testsuite"):
            if len(suite) == 0:
                continue

            name = suite.get('name')
            if name is None:
                continue

            suite_name = name.split('.')
            if len(suite_name) < 2:
                continue

            file_name = suite_name[0] + ".feature"
            class_name = suite_name[1]
            suite.attrib.update({"filepath": file_name})

            for case in suite:
                case.attrib.update({"classname": class_name})

        return tree

    client.junitxml_parse_func = parse_func
    client.run()


@smart_tests.subset
def subset(client: Subset):
    for t in client.stdin():
        if 0 < t.find(".feature"):
            paths = os.path.split(t)
            if len(paths) < 2:
                continue

            file = paths[1]
            client.test_path(file.rstrip('\n'))

    client.separator = "|"
    client.run()

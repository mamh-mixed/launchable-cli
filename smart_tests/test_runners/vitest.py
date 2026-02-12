import xml.etree.ElementTree as ET
from typing import Annotated, List, cast

import smart_tests.args4p.typer as typer

from ..commands.record.tests import RecordTests
from . import smart_tests


@smart_tests.record.tests
def record_tests(
    client: RecordTests,
    reports: Annotated[List[str], typer.Argument(
        multiple=True,
        help="Test report files to process"
    )],
):
    def parse_func(report: str) -> ET.ElementTree:
        """
        Vitest junit report doesn't set file/filepath attributes on test cases, and it's set as a classname attribute instead.
        So, set the classname value as the file name in this function.
        e.g.) <testcase classname="src/components/Hello.test.tsx" name="renders hello message" time="0.008676833">
          """
        tree = cast(ET.ElementTree, ET.parse(report))
        root = tree.getroot()

        if root is None:
            return tree

        for test_suite in root.findall('testsuite'):
            for test_case in test_suite.findall('testcase'):
                classname = test_case.get('classname', '')
                test_case.set('file', classname)
                test_case.attrib.pop('classname', None)

        return tree

    client.junitxml_parse_func = parse_func
    smart_tests.CommonRecordTestImpls.load_report_files(client=client, source_roots=reports)


subset = smart_tests.CommonSubsetImpls(__name__).scan_stdin()

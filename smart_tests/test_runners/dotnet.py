import glob
import os
from typing import Annotated, List
from urllib.parse import unquote

import click
from junitparser import TestCase, TestSuite  # type: ignore

import smart_tests.args4p.typer as typer
from smart_tests.commands.record.tests import RecordTests
from smart_tests.commands.subset import Subset
from smart_tests.test_runners import smart_tests
from smart_tests.test_runners.nunit import nunit_parse_func
from smart_tests.testpath import TestPath

NUNIT_FORMAT = "nunit"
JUNIT_FORMAT = "junit"
SUPPORTED_FORMATS = (JUNIT_FORMAT, NUNIT_FORMAT)


# main subset logic
def do_subset(client: Subset, bare):
    if bare:
        separator = "\n"
        prefix = ""
    else:
        # LEGACY: we recommend the bare mode with native NUnit integration
        # ref: https://github.com/Microsoft/vstest-docs/blob/main/docs/filter.md
        separator = "|"
        prefix = "FullyQualifiedName="

        if client.is_output_exclusion_rules:
            separator = "&"
            prefix = "FullyQualifiedName!="

    def formatter(test_path: TestPath):
        paths = []

        for path in test_path:
            t = path.get("type", "")
            if t == 'Assembly':
                continue
            if t == 'ParameterizedMethod':
                # For parameterized test, we get something like
                # Assembly=calc.dll#TestSuite=SomeNamespace#TestSuite=TestClassName#ParameterizedMethod=DivideTest#TestCase=DivideTest(1,3)
                # see record_test_result.json as an example.
                continue
            paths.append(path.get("name", ""))

        return prefix + ".".join(paths)

    def exclusion_output_handler(subset_tests: List[TestPath], rest_tests: List[TestPath]):
        if client.rest:
            with open(client.rest, "w+", encoding="utf-8") as fp:
                fp.write(client.separator.join(formatter(t) for t in subset_tests))

        click.echo(client.separator.join(formatter(t) for t in rest_tests))

    client.separator = separator
    client.formatter = formatter
    client.exclusion_output_handler = exclusion_output_handler
    client.run()


@smart_tests.subset
def subset(
    client: Subset,
    bare: Annotated[bool, typer.Option(
        "--bare",
        help="outputs class names alone"
    )] = False,
):
    """
    Alpha: Supports only Zero Input Subsetting
    """
    if not client.is_get_tests_from_previous_sessions:
        click.secho(
            "The dotnet profile only supports Zero Input Subsetting.\nMake sure to use "
            "`--get-tests-from-previous-sessions` option",
            fg='red',
            err=True)
        raise typer.Exit(1)

    do_subset(client, bare)


def _clean_field(value):
    """
    Trim tab and other characters that are not appropriate as part of a test path.
    """
    if not value:
        return value
    for token in value.split("\t"):
        token = token.strip()
        if token:
            return unquote(token)
    return ""


def _junit_path_builder(file_path_normalizer):
    """
    Build a TestPath from a JUnit <testcase> element so the resulting structure
    matches the one produced by the NUnit parser:

        Assembly -> TestSuite -> ... -> TestSuite -> TestCase

    Assembly is taken from the <testsuite> name (e.g. "rocket-car-dotnet.dll")
    that `dotnet test --logger junit` emits.
    """

    def build(case: TestCase, suite: TestSuite, report_file: str) -> TestPath:
        test_path: TestPath = []

        assembly = _clean_field(suite._elem.attrib.get("name"))
        if assembly:
            test_path.append({"type": "Assembly", "name": assembly})

        classname = case._elem.attrib.get("classname") or suite._elem.attrib.get("classname")
        classname = _clean_field(classname)
        if classname:
            for part in classname.split("."):
                if part:
                    test_path.append({"type": "TestSuite", "name": part})

        case_name = _clean_field(case._elem.attrib.get("name"))
        if case_name:
            test_path.append({"type": "TestCase", "name": case_name})

        return test_path

    return build


@smart_tests.record.tests
def record_tests(
    client: RecordTests,
    files: Annotated[List[str], typer.Argument(
        multiple=True,
        help="Test report files to process"
    )],
    format: Annotated[str, typer.Option(
        "--format",
        help=f"Test report format. One of: {', '.join(SUPPORTED_FORMATS)}.",
    )] = JUNIT_FORMAT,
):
    """
    Alpha: Supports JUnit (default) and NUnit report formats.
    """
    if format not in SUPPORTED_FORMATS:
        click.secho(
            f"Unsupported --format value: {format}. Supported formats: {', '.join(SUPPORTED_FORMATS)}",
            fg='red',
            err=True)
        raise typer.Exit(1)

    for file in files:
        match = False
        for t in glob.iglob(file, recursive=True):
            match = True
            if os.path.isdir(t):
                client.scan(t, "*.xml")
            else:
                client.report(t)
        if not match:
            click.echo(f"No matches found: {file}", err=True)

    if format == NUNIT_FORMAT:
        client.parse_func = nunit_parse_func
    else:
        client.path_builder = _junit_path_builder(client.file_path_normalizer)
        client.junitxml_parse_func = None

    client.run()

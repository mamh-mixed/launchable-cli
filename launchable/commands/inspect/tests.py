import json
import os
import sys
from abc import ABCMeta, abstractmethod
from http import HTTPStatus
from typing import List

import click
from tabulate import tabulate

from ...utils.env_keys import REPORT_ERROR_KEY
from ...utils.launchable_client import LaunchableClient
from ...utils.session import parse_session
from ..helper import require_session


class TestResult(object):
    def __init__(self, result: dict):
        self._status = result.get("status", "")
        self._duration_sec = result.get("duration", 0.0)
        self._created_at = result.get("createdAt", None)
        self._test_path = "#".join([path["type"] + "=" + path["name"]
                                   for path in result["testPath"] if path.keys() >= {"type", "name"}])


class TestResults(object):
    def __init__(self, results: List[TestResult]):
        self._results = results

    def add(self, result: TestResult):
        self._results.append(result)

    def list(self) -> List[TestResult]:
        return self._results

    def total_duration_sec(self) -> float:
        return sum([result._duration_sec for result in self._results])

    def total_duration_min(self) -> float:
        return (sum([result._duration_sec for result in self._results]) / 60)

    def total_count(self) -> int:
        return len(self._results)

    def filter_by_status(self, status: str) -> 'TestResults':
        return TestResults([result for result in self._results if result._status == status])


class TestResultAbstractDisplay(metaclass=ABCMeta):
    def __init__(self, results: TestResults):
        self._results = results

    @abstractmethod
    def display(self):
        raise NotImplementedError("display method is not implemented")


class TestResultJSONDisplay(TestResultAbstractDisplay):
    def __init__(self, results: TestResults):
        super().__init__(results)

    def display(self):
        result_json = {}
        result_json["summary"] = {
            "total": {
                "report_count": self._results.total_count(),
                "duration_min": self._results.total_duration_min(),
            },
            "success": {
                "report_count": self._results.filter_by_status("SUCCESS").total_count(),
                "duration_min": self._results.filter_by_status("SUCCESS").total_duration_min()
            },
            "failure": {
                "report_count": self._results.filter_by_status("FAILURE").total_count(),
                "duration_min": self._results.filter_by_status("FAILURE").total_duration_min()
            },
            "skip": {
                "report_count": self._results.filter_by_status("SKIPPED").total_count(),
                "duration_min": self._results.filter_by_status("SKIPPED").total_duration_min()
            }
        }
        result_json["results"] = []
        for result in self._results.list():
            result_json["results"].append({
                "test_path": result._test_path,
                "duration_sec": result._duration_sec,
                "status": result._status,
                "created_at": result._created_at
            })

        click.echo(json.dumps(result_json, indent=2))


class TestResultTableDisplay(TestResultAbstractDisplay):
    def __init__(self, results: TestResults):
        super().__init__(results)

    def display(self):
        header = ["Test Path",
                  "Duration (sec)", "Status", "Uploaded At"]
        rows = []
        for result in self._results.list():
            rows.append(
                [
                    result._test_path,
                    result._duration_sec,
                    result._status,
                    result._created_at,
                ]
            )
        click.echo(tabulate(rows, header, tablefmt="github", floatfmt=".2f"))

        summary_header = ["Summary", "Report Count", "Total Duration (min)"]
        summary_rows = [
            ["Total", self._results.total_count(),
             self._results.total_duration_min()],
            ["Success", self._results.filter_by_status("SUCCESS").total_count(),
             self._results.filter_by_status("SUCCESS").total_duration_min()],
            ["Failure", self._results.filter_by_status("FAILURE").total_count(),
             self._results.filter_by_status("FAILURE").total_duration_min()],
            ["Skip", self._results.filter_by_status("SKIPPED").total_count(),
             self._results.filter_by_status("SKIPPED").total_duration_min()]]

        click.echo(tabulate(summary_rows, summary_header, tablefmt="grid", floatfmt=["", ".0f", ".2f"]))


@click.command()
@click.option(
    '--test-session-id',
    'test_session_id',
    help='test session id',
)
@click.option(
    '--json',
    'is_json_format',
    help='display JSON format',
    is_flag=True
)
@click.pass_context
def tests(context: click.core.Context, test_session_id: int, is_json_format: bool):
    if (test_session_id is None):
        try:
            session = require_session(None)
            _, test_session_id = parse_session(session)
        except Exception as e:
            raise click.UsageError(
                click.style(
                    "test session id requires.\n"
                    "Use the --test-session-id or execute after `launchable recrod tests` command.",
                    fg="yellow"))

    try:
        client = LaunchableClient(app=context.obj)
        res = client.request(
            "get", "/test_sessions/{}/events".format(test_session_id))

        if res.status_code == HTTPStatus.NOT_FOUND:
            click.echo(click.style(
                "Test session {} not found. Check test session ID and try again.".format(test_session_id), 'yellow'),
                err=True,
            )
            sys.exit(1)

        res.raise_for_status()
        results = res.json()
    except Exception as e:
        if os.getenv(REPORT_ERROR_KEY):
            raise e
        else:
            click.echo(e, err=True)
        click.echo(click.style(
            "Warning: failed to inspect tests", fg='yellow'),
            err=True)

        return

    test_results = TestResults([])
    for result in results:
        if result.keys() >= {"testPath"}:
            test_results.add(TestResult(result))

    displayer = StdOutTestResultDisplay(test_results)
    if is_json_format:
        displayer = JSONTestResultDisplay(test_results)

    displayer.display()

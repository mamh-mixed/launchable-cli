import os
from enum import Enum
from typing import Annotated

import click

import smart_tests.args4p.typer as typer
from smart_tests import args4p
from smart_tests.app import Application
from smart_tests.commands.test_path_writer import TestPathWriter
from smart_tests.testpath import unparse_test_path
from smart_tests.utils.commands import Command
from smart_tests.utils.env_keys import REPORT_ERROR_KEY
from smart_tests.utils.exceptions import print_error_and_die
from smart_tests.utils.session import get_session
from smart_tests.utils.smart_tests_client import SmartTestsClient
from smart_tests.utils.tracking import Tracking, TrackingClient
from smart_tests.utils.typer_types import ignorable_error


class DetectFlakesRetryThreshold(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

    @staticmethod
    def from_str(value: str) -> "DetectFlakesRetryThreshold":
        for member in DetectFlakesRetryThreshold:
            if member.value.lower() == value.lower():
                return member
        raise ValueError(f"Invalid value for DetectFlakesRetryThreshold: {value}")


@args4p.group(help="Detect flaky tests")
def detect_flakes(
    app: Application,
    session: Annotated[str, typer.Option(
        "--session",
        help="In the format builds/<build-name>/test_sessions/<test-session-id>",
        metavar="SESSION"
    )],
    retry_threshold: Annotated[DetectFlakesRetryThreshold, typer.Option(
        "--retry-threshold",
        help="Thoroughness of how \"flake\" is detected",
        type=DetectFlakesRetryThreshold.from_str,
        metavar="low|medium|high"
    )] = DetectFlakesRetryThreshold.MEDIUM,
    test_runner: Annotated[str | None, typer.Argument()] = None,
):
    tracking_client = TrackingClient(Command.DETECT_FLAKE, app=app)
    app.test_runner = test_runner
    client = SmartTestsClient(app=app, tracking_client=tracking_client)

    test_session = None
    try:
        test_session = get_session(client=client, session=session)
    except ValueError as e:
        print_error_and_die(msg=str(e), tracking_client=tracking_client, event=Tracking.ErrorEvent.USER_ERROR)
    except Exception as e:
        if os.getenv(REPORT_ERROR_KEY):
            raise e
        else:
            click.echo(ignorable_error(e), err=True)

    if test_session is None:
        return

    class FlakeDetection(TestPathWriter):
        def __init__(self):
            super(FlakeDetection, self).__init__(app)

        def run(self):
            test_paths = []
            try:
                res = client.request(
                    "get",
                    "detect-flake",
                    params={
                        "confidence": retry_threshold.value.upper(),
                        "session-id": os.path.basename(session),
                        "test-runner": app.test_runner,
                    })

                res.raise_for_status()
                test_paths = res.json().get("testPaths", [])
                if test_paths:
                    self.print(test_paths)
                    click.echo("Trying to retry the following tests:", err=True)
                    for detail in res.json().get("testDetails", []):
                        click.echo(f"{detail.get('reason'): {unparse_test_path(detail.get('fullTestPath'))}}", err=True)
            except Exception as e:
                tracking_client.send_error_event(
                    event_name=Tracking.ErrorEvent.INTERNAL_CLI_ERROR,
                    stack_trace=str(e),
                )
                if os.getenv(REPORT_ERROR_KEY):
                    raise e
                else:
                    click.echo(ignorable_error(e), err=True)

    return FlakeDetection()

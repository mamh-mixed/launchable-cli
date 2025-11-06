import os
from enum import Enum
from typing import Annotated

import click

import smart_tests.args4p.typer as typer
from smart_tests.app import Application
from smart_tests.args4p.command import Group
from smart_tests.commands.test_path_writer import TestPathWriter
from smart_tests.testpath import unparse_test_path
from smart_tests.utils.commands import Command
from smart_tests.utils.env_keys import REPORT_ERROR_KEY
from smart_tests.utils.exceptions import print_error_and_die
from smart_tests.utils.session import SessionId, get_session
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


class DetectFlakes(TestPathWriter):
    def __init__(
            self,
            app: Application,
            session: Annotated[SessionId, SessionId.as_option()],
            retry_threshold: Annotated[DetectFlakesRetryThreshold, typer.Option(
                "--retry-threshold",
                help="Thoroughness of how \"flake\" is detected",
                type=DetectFlakesRetryThreshold.from_str,
                metavar="low|medium|high"
            )] = DetectFlakesRetryThreshold.MEDIUM,
            test_runner: Annotated[str | None, typer.Argument()] = None,
    ):
        super().__init__(app)

        app.test_runner = test_runner
        self.tracking_client = TrackingClient(Command.DETECT_FLAKE, app=app)
        self.client = SmartTestsClient(app=app, tracking_client=self.tracking_client)

        self.session = session
        self.test_session = None
        try:
            self.test_session = get_session(client=self.client, session=session)
        except ValueError as e:
            print_error_and_die(msg=str(e), tracking_client=self.tracking_client, event=Tracking.ErrorEvent.USER_ERROR)
        except Exception as e:
            if os.getenv(REPORT_ERROR_KEY):
                raise e
            else:
                click.echo(ignorable_error(e), err=True)

        if self.test_session is None:
            raise typer.Exit(0)     # bail out

        self.retry_threshold = retry_threshold

    def run(self):
        test_paths = []
        try:
            res = self.client.request(
                "get",
                "detect-flake",
                params={
                    "confidence": self.retry_threshold.value.upper(),
                    "session-id": self.session.test_part,
                    "test-runner": self.app.test_runner,
                })

            res.raise_for_status()
            test_paths = res.json().get("testPaths", [])
            if test_paths:
                self.print(test_paths)
                click.echo("Trying to retry the following tests:", err=True)
                for detail in res.json().get("testDetails", []):
                    click.echo(f"{detail.get('reason'): {unparse_test_path(detail.get('fullTestPath'))}}", err=True)
        except Exception as e:
            self.tracking_client.send_error_event(
                event_name=Tracking.ErrorEvent.INTERNAL_CLI_ERROR,
                stack_trace=str(e),
            )
            if os.getenv(REPORT_ERROR_KEY):
                raise e
            else:
                click.echo(ignorable_error(e), err=True)


detect_flakes = Group(name="detect-flakes", callback=DetectFlakes, help="Detect flaky tests")

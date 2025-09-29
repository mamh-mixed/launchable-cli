import os
from enum import Enum
from typing import Annotated

import typer

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


app = typer.Typer(name="detect-flakes", help="Detect flaky tests")


@app.callback()
def detect_flakes(
    ctx: typer.Context,
    session: Annotated[str, typer.Option(
        "--session",
        help="In the format builds/<build-name>/test_sessions/<test-session-id>",
        metavar="SESSION"
    )],
    retry_threshold: Annotated[DetectFlakesRetryThreshold, typer.Option(
        "--retry-threshold",
        help="Thoroughness of how \"flake\" is detected",
        case_sensitive=False,
        show_default=True,
    )] = DetectFlakesRetryThreshold.MEDIUM,
):
    app = ctx.obj
    tracking_client = TrackingClient(Command.DETECT_FLAKE, app=app)
    test_runner = getattr(ctx, 'test_runner', None)
    client = SmartTestsClient(app=app, tracking_client=tracking_client, test_runner=test_runner)

    test_session = None
    try:
        test_session = get_session(client=client, session=session)
    except ValueError as e:
        print_error_and_die(msg=str(e), tracking_client=tracking_client, event=Tracking.ErrorEvent.USER_ERROR)
    except Exception as e:
        if os.getenv(REPORT_ERROR_KEY):
            raise e
        else:
            typer.echo(ignorable_error(e), err=True)

    if test_session is None:
        return

    class FlakeDetection(TestPathWriter):
        def __init__(self, app: Application):
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
                        "test-runner": test_runner,
                    })

                res.raise_for_status()
                test_paths = res.json().get("testPaths", [])
                if test_paths:
                    self.print(test_paths)
                    typer.echo("Trying to retry the following tests:", err=True)
                    for detail in res.json().get("testDetails", []):
                        typer.echo(f"{detail.get('reason'): {unparse_test_path(detail.get('fullTestPath'))}}", err=True)
            except Exception as e:
                tracking_client.send_error_event(
                    event_name=Tracking.ErrorEvent.INTERNAL_CLI_ERROR,
                    stack_trace=str(e),
                )
                if os.getenv(REPORT_ERROR_KEY):
                    raise e
                else:
                    typer.echo(ignorable_error(e), err=True)

    ctx.obj = FlakeDetection(app=ctx.obj)

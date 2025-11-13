from typing import Annotated, List

import click

import smart_tests.args4p.typer as typer
from smart_tests.utils.session import SessionId, get_session

from ... import args4p
from ...app import Application
from ...utils.fail_fast_mode import warn_and_exit_if_fail_fast_mode
from ...utils.smart_tests_client import SmartTestsClient


@args4p.command(help="Record attachment information")
def attachment(
    app: Application,
    session: Annotated[SessionId, SessionId.as_option()],
    attachments: Annotated[List[str], typer.Argument(
        multiple=True,
        help="Attachment files to upload"
    )],
):
    client = SmartTestsClient(app=app)
    try:
        # Note: Call get_session method to check test session exists
        _ = get_session(session, client)
        for a in attachments:
            click.echo(f"Sending {a}")
            try:
                with open(a, mode='rb') as f:
                    res = client.request(
                        "post", session.subpath('attachment'), compress=True, payload=f,
                        additional_headers={"Content-Disposition": f"attachment;filename=\"{a}\""})
                    res.raise_for_status()
            except OSError as e:
                # no such file, permission error, etc.
                # report, then continue to next attachment file
                warn_and_exit_if_fail_fast_mode(str(e))
    except Exception as e:
        client.print_exception_and_recover(e)

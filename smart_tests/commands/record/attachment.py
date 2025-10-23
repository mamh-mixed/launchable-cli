from typing import Annotated, List

import click

import smart_tests.args4p.typer as typer
from smart_tests.utils.session import get_session

from ... import args4p
from ...app import Application
from ...utils.smart_tests_client import SmartTestsClient


@args4p.command(help="Record attachment information")
def attachment(
    app: Application,
    session: Annotated[str, typer.Option(
        "--session",
        help="test session name",
        required=True
    )],
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
            with open(a, mode='rb') as f:
                res = client.request(
                    "post", f"{session}/attachment", compress=True, payload=f,
                    additional_headers={"Content-Disposition": f"attachment;filename=\"{a}\""})
                res.raise_for_status()
    except Exception as e:
        client.print_exception_and_recover(e)

from typing import Annotated, List

import typer

from smart_tests.utils.session import get_session

from ...utils.smart_tests_client import SmartTestsClient

app = typer.Typer(name="attachment", help="Record attachment information")


@app.callback(invoke_without_command=True)
def attachment(
    ctx: typer.Context,
    session: Annotated[str, typer.Option(
        "--session",
        help="test session name"
    )],
    attachments: Annotated[List[str], typer.Argument(
        help="Attachment files to upload"
    )],
):
    app = ctx.obj
    client = SmartTestsClient(app=app)
    try:
        # Note: Call get_session method to check test session exists
        _ = get_session(session, client)
        for a in attachments:
            typer.echo(f"Sending {a}")
            with open(a, mode='rb') as f:
                res = client.request(
                    "post", f"{session}/attachment", compress=True, payload=f,
                    additional_headers={"Content-Disposition": f"attachment;filename=\"{a}\""})
                res.raise_for_status()
    except Exception as e:
        client.print_exception_and_recover(e)

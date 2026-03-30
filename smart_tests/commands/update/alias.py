from typing import Annotated

import click

import smart_tests.args4p.typer as typer
from smart_tests import args4p
from smart_tests.app import Application
from smart_tests.utils.commands import Command
from smart_tests.utils.fail_fast_mode import set_fail_fast_mode, warn_and_exit_if_fail_fast_mode
from smart_tests.utils.smart_tests_client import SmartTestsClient
from smart_tests.utils.tracking import TrackingClient


@args4p.command(help="Point an alias at a build")
def alias(
    app: Application,
    build_name: Annotated[str, typer.Option(
        "--build",
        help="Build name to point the alias at",
        metavar="NAME",
        required=True,
    )],
    alias_name: Annotated[str, typer.Option(
        "--alias",
        help="Alias name",
        metavar="NAME",
        required=True,
    )],
):
    tracking_client = TrackingClient(Command.UPDATE_ALIAS, app=app)
    client = SmartTestsClient(app=app, tracking_client=tracking_client)
    set_fail_fast_mode(client.is_fail_fast_mode())

    # TODO: It's not entirely clear to me which layer is responsible for URL encoding
    # this validation logic was copied from record/build.py
    if "/" in alias_name or "%2f" in alias_name.lower():
        click.echo("--alias must not contain a slash and an encoded slash", err=True)
        raise typer.Exit(1)
    if "%25" in alias_name:
        click.echo("--alias must not contain encoded % (%25)", err=True)
        raise typer.Exit(1)

    try:
        res = client.request("put", f"builds/aliases/{alias_name}", payload={"build": build_name})
        res.raise_for_status()
        click.echo(f"Alias '{alias_name}' now points to build '{build_name}'")
    except Exception as e:
        warn_and_exit_if_fail_fast_mode(f"Failed to update alias: {e}")

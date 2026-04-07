from typing import Annotated

import click

import smart_tests.args4p.typer as typer
from smart_tests import args4p
from smart_tests.app import Application
from smart_tests.utils.commands import Command
from smart_tests.utils.fail_fast_mode import set_fail_fast_mode, warn_and_exit_if_fail_fast_mode
from smart_tests.utils.smart_tests_client import SmartTestsClient
from smart_tests.utils.tracking import TrackingClient


@args4p.command(help="Record a deployment (sets alias deployment:{environment}:{service} -> build)")
def deployment(
    app: Application,
    build_name: Annotated[str, typer.Option(
        "--build",
        help="Build name",
        metavar="NAME",
        required=True,
    )],
    environment: Annotated[str, typer.Option(
        "--environment",
        help="Deployment environment name",
        metavar="NAME",
        required=True,
    )],
    service: Annotated[str, typer.Option(
        "--service",
        help="Service name",
        metavar="NAME",
        required=True,
    )],
):
    alias_name = f"deployment:{environment}:{service}"

    tracking_client = TrackingClient(Command.RECORD_DEPLOYMENT, app=app)
    client = SmartTestsClient(app=app, tracking_client=tracking_client)
    set_fail_fast_mode(client.is_fail_fast_mode())

    try:
        res = client.request("put", f"builds/aliases/{alias_name}", payload={"build": build_name})
        res.raise_for_status()
        click.echo(f"Deployment of '{service}' in '{environment}' now points to build '{build_name}'")
    except Exception as e:
        warn_and_exit_if_fail_fast_mode(f"Failed to record deployment: {e}")

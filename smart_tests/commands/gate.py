import json
import sys
from http import HTTPStatus
from typing import Annotated

import click
from requests import Response
from tabulate import tabulate

from smart_tests.utils.tracking import TrackingClient
from .. import args4p
from ..app import Application
from ..args4p import typer

from ..utils.commands import Command
from ..utils.session import SessionId
from ..utils.smart_tests_client import SmartTestsClient


@args4p.command()
def gate(app_instance: Application,
         session: Annotated[SessionId, SessionId.as_option()],
         is_json_format: Annotated[bool, typer.Option(
                "--json",
                help="display JSON format")] = False):
    tracking_client = TrackingClient(Command.GATE, app=app_instance)
    client = SmartTestsClient(tracking_client=tracking_client, app=app_instance)
    try:
        res: Response = client.request("get", "gate", params={"session-id": session.test_part})

        if res.status_code == HTTPStatus.NOT_FOUND:
            click.echo(click.style(
                "Gate data currently not available for this workspace.", 'yellow'), err=True)
            sys.exit()

        res.raise_for_status()

        res_json = res.json()

        if is_json_format:
            display_as_json(res)
        else:
            display_as_table(res)

        # Exit with failure status if gate failed
        if res_json.get('status') == 'FAILED':
            sys.exit(1)

    except Exception as e:
        client.print_exception_and_recover(e, "Warning: failed to fetch gate status")


def display_as_json(res: Response):
    res_json = res.json()
    click.echo(json.dumps(res_json, indent=2))


def display_as_table(res: Response):
    headers = ["Status", "Quarantined (Ignored)", "Actionable Failures"]
    res_json = res.json()

    status_icon = "PASSED" if res_json.get('status') == 'PASSED' else "FAILED"

    rows = [[
        status_icon,
        res_json.get('quarantinedFailures', 0),
        res_json.get('actionableFailures', 0)
    ]]

    click.echo(tabulate(rows, headers, tablefmt="github"))

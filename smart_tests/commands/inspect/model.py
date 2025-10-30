import json
import sys
from http import HTTPStatus
from typing import Annotated

import click
from requests import Response
from tabulate import tabulate

from smart_tests import args4p
from smart_tests.app import Application
from smart_tests.args4p import typer
from smart_tests.utils.smart_tests_client import SmartTestsClient


@args4p.command()
def model(
        app: Application,
        is_json_format: Annotated[bool, typer.Option(
            '--json',
            help="display JSON format"
        )] = False):
    client = SmartTestsClient(app=app)
    try:
        res: Response = client.request("get", "model-metadata")

        if res.status_code == HTTPStatus.NOT_FOUND:
            click.echo(click.style(
                "Model metadata currently not available for this workspace.", 'yellow'), err=True)
            sys.exit()

        res.raise_for_status()

        if is_json_format:
            display_as_json(res)
        else:
            display_as_table(res)

    except Exception as e:
        client.print_exception_and_recover(e, "Warning: failed to inspect model")


def display_as_json(res: Response):
    res_json = res.json()
    click.echo(json.dumps(res_json, indent=2))


def display_as_table(res: Response):
    headers = ["Metadata", "Value"]
    res_json = res.json()
    rows = [["Training Cutoff Test Session ID", res_json['training_cutoff_test_session_id']]]
    click.echo(tabulate(rows, headers, tablefmt="github"))

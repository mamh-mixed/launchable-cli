from typing import Annotated, Any, Dict, List

import click

import smart_tests.args4p.typer as typer

from ... import args4p
from ...app import Application
from ...utils.smart_tests_client import SmartTestsClient
from ...utils.typer_types import validate_key_value


@args4p.command(help="View test session statistics")
def test_sessions(
    app: Application,
    days: Annotated[int, typer.Option(
        help="How many days of test sessions in the past to be stat"
    )] = 7,
    flavor: Annotated[List[str], typer.Option(
        multiple=True,
        help="flavors",
        metavar="KEY=VALUE"
    )] = [],
):
    # Parse flavors
    parsed_flavors = [validate_key_value(f) for f in flavor]

    params: Dict[str, Any] = {'days': days, 'flavor': []}
    flavors = []
    for f in parsed_flavors:
        flavors.append('%s=%s' % (f[0], f[1]))

    if flavors:
        params['flavor'] = flavors
    else:
        params.pop('flavor', None)

    client = SmartTestsClient(app=app)
    try:
        res = client.request('get', '/stats/test-sessions', params=params)
        res.raise_for_status()
        click.echo(res.text)

    except Exception as e:
        client.print_exception_and_recover(e, "Warning: the service failed to get stat.")

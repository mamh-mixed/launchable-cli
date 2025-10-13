from typing import Annotated, List

import click

import smart_tests.args4p.typer as typer
from smart_tests.test_runners import smart_tests


@smart_tests.record.tests
def record_tests(
    client,
    reports: Annotated[List[str], typer.Argument(
        multiple=True,
        help="Test report files to process"
    )],
):
    for r in reports:
        click.echo(f'foo:{r}')


@smart_tests.subset
def subset(client):
    click.echo("Subset!")

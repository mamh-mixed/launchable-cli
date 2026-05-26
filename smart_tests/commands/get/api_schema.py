import importlib.resources
import shutil
import sys
from pathlib import Path

import click

from smart_tests import args4p
from smart_tests.app import Application

OUTPUT_FILE = 'openapi-schema.json'


@args4p.command(help="Copy OpenAPI schema to ./openapi-schema.json")
def api_schema(app: Application):
    output = Path(OUTPUT_FILE)
    if output.exists():
        click.secho(
            f"'{OUTPUT_FILE}' already exists. Please delete it first, then re-run this command.",
            fg='red', err=True,
        )
        sys.exit(1)

    # Copy bundled schema file to current directory
    schema_src = Path(str(importlib.resources.files('smart_tests') / 'schema' / 'openapi-schema.json'))
    click.echo(f"Copying OpenAPI schema to ./{OUTPUT_FILE} ...")
    shutil.copy(schema_src, output)
    click.echo(f"Done. OpenAPI schema is in ./{OUTPUT_FILE}")

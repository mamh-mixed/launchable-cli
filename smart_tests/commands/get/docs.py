import importlib.resources
import shutil
import sys
from pathlib import Path

import click

from ... import args4p
from ...app import Application

OUTPUT_DIR = 'smart-tests-docs'


@args4p.command(help="Copy product documentation into ./smart-tests-docs")
def docs(app: Application):
    output = Path(OUTPUT_DIR)
    if output.exists():
        click.secho(
            f"'{OUTPUT_DIR}' already exists. Please delete it first, then re-run this command.",
            fg='red', err=True,
        )
        sys.exit(1)

    docs_src = Path(str(importlib.resources.files('smart_tests') / 'docs'))
    click.echo(f"Copying docs to ./{OUTPUT_DIR} ...")
    shutil.copytree(docs_src, output)
    click.echo(f"Done. Documentation is in ./{OUTPUT_DIR}")

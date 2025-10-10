import smart_tests.args4p.typer as typer

from . import subset
from ... import args4p
from ...app import Application
from .subset import subset


@args4p.group(help="Inspect test and subset data")
def inspect(app :Application):
    return app


inspect.add_command(subset)

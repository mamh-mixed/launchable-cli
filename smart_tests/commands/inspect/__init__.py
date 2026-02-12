from ... import args4p
from ...app import Application
from .model import model
from .subset import subset


@args4p.group(help="Inspect test and subset data")
def inspect(app: Application):
    return app


inspect.add_command(model)
inspect.add_command(subset)

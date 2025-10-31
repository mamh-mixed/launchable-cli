from .model import model
from .tests import tests
from ... import args4p
from ...app import Application
from .subset import subset


@args4p.group(help="Inspect test and subset data")
def inspect(app: Application):
    return app


inspect.add_command(model)
inspect.add_command(subset)
inspect.add_command(tests)

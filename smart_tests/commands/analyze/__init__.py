from ... import args4p
from ...app import Application
from .subset import subset


@args4p.group()
def analyze(app: Application):
    return app


analyze.add_command(subset)

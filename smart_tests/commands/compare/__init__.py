from ... import args4p
from ...app import Application
from .subsets import subsets


@args4p.group()
def compare(app: Application):
    return app


compare.add_command(subsets)

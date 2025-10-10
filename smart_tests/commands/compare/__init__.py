from .subsets import subsets
from ... import args4p
from ...app import Application


@args4p.group()
def compare(app : Application):
    return app

compare.add_command(subsets)

from ... import args4p
from ...app import Application
from .alias import alias


@args4p.group(help="Update Smart Tests resources")
def update(app: Application):
    return app


update.add_command(alias)

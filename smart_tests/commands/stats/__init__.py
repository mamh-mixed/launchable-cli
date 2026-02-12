from ... import args4p
from ...app import Application
from .test_sessions import test_sessions


@args4p.group()
def stats(app: Application):
    return app


stats.add_command(test_sessions)

import smart_tests.args4p.typer as typer

from . import test_sessions

app = typer.Typer(name="stats", help="View test session statistics")

app.add_typer(test_sessions.app, name="test-sessions")

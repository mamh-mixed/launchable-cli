from ... import args4p
from ...app import Application
from .flaky_tests import flaky_tests
from .test_results import test_results


@args4p.group(help="View historical test data and insights")
def view(app: Application):
    return app


view.add_command(flaky_tests)
view.add_command(test_results)

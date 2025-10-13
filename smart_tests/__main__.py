import importlib
import importlib.util
import logging
import os
import sys
from glob import glob
from os.path import basename, dirname, join
from typing import Annotated

import click

import smart_tests.args4p.typer as typer
from smart_tests import args4p
from smart_tests.app import Application
from .commands.compare import compare
from .commands.detect_flakes import detect_flakes
from .commands.inspect import inspect
from .commands.record import record
from .commands.stats import stats
from .commands.subset import subset
from .commands.verify import verify
from .utils import logger
from .utils.env_keys import SKIP_CERT_VERIFICATION
from .version import __version__


@args4p.group()
def main(
    log_level: Annotated[str, typer.Option(
        help="Set logger's log level (CRITICAL, ERROR, WARNING, AUDIT, INFO, DEBUG)."
    )] = logger.LOG_LEVEL_DEFAULT_STR,
    plugin_dir: Annotated[str | None, typer.Option(
        "--plugins",
        help="Directory to load plugins from"
    )] = None,
    dry_run: Annotated[bool, typer.Option(
        help="Dry-run mode. No data is sent to the server. However, sometimes "
             "GET requests without payload data or side effects could be sent."
             "note: Since the dry run log is output together with the AUDIT log, "
             "even if the log-level is set to warning or higher, the log level will "
             "be forced to be set to AUDIT."
    )] = False,
    skip_cert_verification: Annotated[bool, typer.Option(
        help="Skip the SSL certificate check. This lets you bypass system setup issues "
             "like CERTIFICATE_VERIFY_FAILED, at the expense of vulnerability against "
             "a possible man-in-the-middle attack. Use it as an escape hatch, but with caution."
    )] = False,
    version: Annotated[bool | None, typer.Option(
        "--version", help="Show version and exit"
    )] = None,
) -> Application:
    if version:
        click.echo(f"smart-tests-cli {__version__}")
        raise typer.Exit(0)


    level = logger.get_log_level(log_level)
    # In the case of dry-run, it is forced to set the level below the AUDIT.
    # This is because the dry-run log will be output along with the audit log.
    if dry_run and level > logger.LOG_LEVEL_AUDIT:
        level = logger.LOG_LEVEL_AUDIT

    if not skip_cert_verification:
        skip_cert_verification = (os.environ.get(SKIP_CERT_VERIFICATION) is not None)

    logging.basicConfig(level=level)

    # plugin_dir is processed earlier. If we do it here, it's too late

    return Application(dry_run=dry_run, skip_cert_verification=skip_cert_verification)

main.add_command(record)
main.add_command(subset)
# TODO: main.add_command(split_subset)
main.add_command(verify)
main.add_command(inspect)
main.add_command(stats)
main.add_command(compare)
main.add_command(detect_flakes)

def _load_test_runners():
    # load all test runners
    for f in glob(join(dirname(__file__), 'test_runners', "*.py")):
        f = basename(f)[:-3]
        if f == '__init__':
            continue
        importlib.import_module(f'smart_tests.test_runners.{f}')

    # load all plugins. Here we do a bit of command line parsing ourselves,
    # because the command line could look something like `smart-tests record tests myprofile --plugins ...
    plugin_dir = None
    if "--plugins" in sys.argv:
        idx = sys.argv.index("--plugins")
        if idx + 1 < len(sys.argv):
            plugin_dir = sys.argv[idx + 1]

    if plugin_dir:
        for f in glob(join(plugin_dir, '*.py')):
            spec = importlib.util.spec_from_file_location(
                f"launchable.plugins.{basename(f)[:-3]}", f)
            plugin = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin)

_load_test_runners()

if __name__ == '__main__':
    try:
        main(sys.argv)
        sys.exit(0)
    except typer.Exit as e:
        sys.exit(e.exit_code)

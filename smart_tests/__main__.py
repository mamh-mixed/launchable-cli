import importlib
import importlib.util
import logging
import os
import sys
from glob import glob
from os.path import basename, dirname, join
from typing import Annotated

import smart_tests.args4p.typer as typer
from smart_tests import args4p

from smart_tests.app import Application
from smart_tests.utils.test_runner_registry import get_registry

from .commands import compare, detect_flakes, inspect, record, stats, subset, verify
from .utils import logger
from .utils.env_keys import SKIP_CERT_VERIFICATION
from .version import __version__

# Load all test runners at module level so they register their commands
for f in glob(join(dirname(__file__), 'test_runners', "*.py")):
    f = basename(f)[:-3]
    if f == '__init__':
        continue
    importlib.import_module('smart_tests.test_runners.%s' % f)


# Global flag to track if plugins have been loaded and commands need rebuilding
_plugins_loaded = False


def _rebuild_nested_commands_with_plugins():
    """Rebuild NestedCommand apps after plugins are loaded."""
    global _plugins_loaded
    if _plugins_loaded:
        return  # Already rebuilt

    try:
        # Clear existing commands from nested apps and rebuild
        for module_name in ['smart_tests.commands.subset', 'smart_tests.commands.record.tests',
                            'smart_tests.commands.detect_flakes']:
            module = importlib.import_module(module_name)
            if hasattr(module, 'nested_command_app'):
                nested_app = module.nested_command_app
                nested_app.registered_commands.clear()
                nested_app.registered_groups.clear()
            if hasattr(module, 'create_nested_commands'):
                module.create_nested_commands()

        _plugins_loaded = True
        logging.info("Successfully rebuilt NestedCommand apps with plugins")

    except Exception as e:
        logging.warning(f"Failed to rebuild NestedCommand apps with plugins: {e}")
        import traceback
        logging.warning(f"Traceback: {traceback.format_exc()}")


# Set up automatic rebuilding when new test runners are registered


def _on_test_runner_registered():
    """Callback triggered when new test runners are registered."""
    _rebuild_nested_commands_with_plugins()


get_registry().set_on_register_callback(_on_test_runner_registered)

def version_callback(value: bool):
    if value:
        click.echo(f"smart-tests-cli {__version__}")
        raise typer.Exit()


@args4p.group()
def main(
    log_level: Annotated[str, typer.Option(
        help="Set logger's log level (CRITICAL, ERROR, WARNING, AUDIT, INFO, DEBUG)."
    )] = logger.LOG_LEVEL_DEFAULT_STR,
    plugin_dir: Annotated[str | None, typer.Option(
        "--plugin-dir", "--plugins",
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
        "--version", help="Show version and exit", callback=version_callback, is_eager=True
    )] = None,
) -> Application:
    level = logger.get_log_level(log_level)
    # In the case of dry-run, it is forced to set the level below the AUDIT.
    # This is because the dry-run log will be output along with the audit log.
    if dry_run and level > logger.LOG_LEVEL_AUDIT:
        level = logger.LOG_LEVEL_AUDIT

    if not skip_cert_verification:
        skip_cert_verification = (os.environ.get(SKIP_CERT_VERIFICATION) is not None)

    logging.basicConfig(level=level)

    # load all plugins
    if plugin_dir:
        for f in glob(join(plugin_dir, '*.py')):
            spec = importlib.util.spec_from_file_location(
                f"smart_tests.plugins.{basename(f)[:-3]}", f)
            if spec is None:
                raise ImportError(f"Failed to create module spec for plugin: {f}")
            if spec.loader is None:
                raise ImportError(f"Plugin spec has no loader: {f}")
            plugin = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin)

    # After loading plugins, rebuild NestedCommand apps to include plugin commands
    if plugin_dir:
        _rebuild_nested_commands_with_plugins()

    return Application(dry_run=dry_run, skip_cert_verification=skip_cert_verification)

main.add_command(record)
main.add_command(subset)
main.add_command(split_subset)
main.add_command(verify)
main.add_command(inspect)
main.add_command(stats)
main.add_command(compare)
main.add_command(detect_flakes)

if __name__ == '__main__':
    try:
        main(sys.argv)
        sys.exit(0)
    except typer.Exit as e:
        sys.exit(e.exit_code)

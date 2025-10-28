# Object representing the most global state possible, which represents a single invocation of CLI
# Currently it's used to keep global configurations.
#
# From command implementations, this is available via dependency injection

import logging
import os
from typing import Annotated

import click

import smart_tests.args4p.typer as typer
from smart_tests.utils import logger
from smart_tests.utils.env_keys import SKIP_CERT_VERIFICATION
from smart_tests.version import __version__


class Application:
    # Group commands that take the CLI profile as a sub-command shall set this parameter
    test_runner: str | None = None

    # this maps to the main entry point of the CLI command
    def __init__(
            self,
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
            version: Annotated[bool, typer.Option(
                "--version", help="Show version and exit"
            )] = False,
    ):
        if version:
            click.echo(f"smart-tests-cli {__version__}")
            raise typer.Exit(0)

        level = logger.get_log_level(log_level)
        # In the case of dry-run, it is forced to set the level below the AUDIT.
        # This is because the dry-run log will be output along with the audit log.
        if dry_run and level > logger.LOG_LEVEL_AUDIT:
            level = logger.LOG_LEVEL_AUDIT
        logging.basicConfig(level=level)

        # plugin_dir is processed earlier. If we do it here, it's too late

        # Dry run mode. This command is used by customers to inspect data we'd send to our server,
        # but without actually doing so.
        self.dry_run = dry_run

        if not skip_cert_verification:
            skip_cert_verification = (os.environ.get(SKIP_CERT_VERIFICATION) is not None)
        self.skip_cert_verification = skip_cert_verification

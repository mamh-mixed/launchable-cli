# Utilities for TestSession.
# Named `session.py` to avoid confusion with test files.

import re
import sys
from dataclasses import dataclass

import click
from requests import HTTPError

from smart_tests.args4p import typer
from smart_tests.args4p.exceptions import BadCmdLineException
from smart_tests.utils.smart_tests_client import SmartTestsClient
from smart_tests.utils.tracking import Tracking


@dataclass
class TestSession:
    id: int
    build_id: int
    build_name: str
    observation_mode: bool
    name: str | None = None


class SessionId:
    '''Represents the user-specific test session via the --session option.'''

    def __init__(self, id: str):
        '''This is the method in which we parse the user input, so be defensive'''
        if id.startswith('@'):
            file_path = id[1:]
            try:
                with open(file_path, 'r') as f:
                    id = f.read().strip()
            except FileNotFoundError:
                raise BadCmdLineException(f"Session file '{file_path}' not found.")
            except IOError as e:
                raise BadCmdLineException(f"Error reading session file '{file_path}': {e}")

        match = re.match(r"builds/([^/]+)/test_sessions/(.+)", id)

        if match:
            self.id = id
            self.build_part = match.group(1)
            self.test_part = int(match.group(2))
        else:
            raise BadCmdLineException(
                f"Invalid session ID. Expecting the output from 'smart-tests record session', but got '{id}'")

    def __str__(self):
        return self.id

    def subpath(self, endpoint: str) -> str:
        return f"{self.id}/{endpoint}"

    @staticmethod
    def as_option():
        '''To promote consistency of the --session option across commands, use this to define an option.'''
        return typer.Option(
            "--session",
            help="Session ID obtained by calling 'smart-tests record session'. It also accepts '@path/to/file' if the session ID is stored in a file ",  # noqa E501
            required=True,
            metavar="SESSION",
            type=SessionId,
        )


def get_session(session: SessionId, client: SmartTestsClient) -> TestSession:
    res = client.request("get", session.id)

    try:
        res.raise_for_status()
    except HTTPError as e:
        if e.response.status_code == 404:
            # TODO(Konboi): move subset.print_error_and_die to util and use it
            msg = f"Session {session} was not found."
            click.secho(msg, fg='red', err=True)
            if client.tracking_client:
                client.tracking_client.send_error_event(event_name=Tracking.ErrorEvent.USER_ERROR, stack_trace=msg)
            sys.exit(1)
        raise

    test_session = res.json()

    return TestSession(
        id=test_session.get("id"),
        build_id=test_session.get("buildId"),
        build_name=test_session.get("buildNumber"),
        observation_mode=test_session.get("isObservation"),
        name=test_session.get("name"),
    )

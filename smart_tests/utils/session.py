# Utilities for TestSession.
# Named `session.py` to avoid confusion with test files.

import re
import sys
from dataclasses import dataclass
from typing import Tuple

import click
from requests import HTTPError

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


def get_session(session: str, client: SmartTestsClient) -> TestSession:
    build_name, test_session_id = parse_session(session)

    subpath = f"builds/{build_name}/test_sessions/{test_session_id}"
    res = client.request("get", subpath)

    try:
        res.raise_for_status()
    except HTTPError as e:
        if e.response.status_code == 404:
            # TODO(Konboi): move subset.print_error_and_die to util and use it
            msg = f"Session {session} was not found. Make sure to run `smart-tests record session --build {build_name}` before you run this command"  # noqa E501
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


def parse_session(session: str) -> Tuple[str, int]:
    """Parse session to extract build name and test session id.

    Args:
        session: Session in format "builds/{build_name}/test_sessions/{test_session_id}"

    Returns:
        Tuple of (build_name, test_session_id)

    Raises:
        ValueError: If session_id format is invalid
    """
    match = re.match(r"builds/([^/]+)/test_sessions/(.+)", session)

    if match:
        return match.group(1), int(match.group(2))
    else:
        raise BadCmdLineException(
            f"Invalid session ID format: {session}. Expected format: builds/{{build_name}}/test_sessions/{{test_session_id}}")

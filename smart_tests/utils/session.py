# Utilities for TestSession.
# Named `session.py` to avoid confusion with test files.

from dataclasses import dataclass
from typing import Tuple

from smart_tests.utils.smart_tests_client import SmartTestsClient


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
    res.raise_for_status()

    test_session = res.json()

    return TestSession(
        id=test_session.get("id"),
        build_id=test_session.get("buildId"),
        build_name=test_session.get("buildNumber"),
        observation_mode=test_session.get("isObservation"),
        name=test_session.get("name"),
    )


def parse_session(session: str) -> Tuple[str, str]:
    """Parse session to extract build name and test session id.

    Args:
        session: Session in format "builds/{build_name}/test_sessions/{test_session_id}"

    Returns:
        Tuple of (build_name, test_session_id)

    Raises:
        ValueError: If session_id format is invalid
    """
    import re
    match = re.match(r"builds/([^/]+)/test_sessions/(.+)", session)
    if match:
        return match.group(1), match.group(2)
    else:
        raise ValueError(
            f"Invalid session ID format: {session}. Expected format: builds/{{build_name}}/test_sessions/{{test_session_id}}")

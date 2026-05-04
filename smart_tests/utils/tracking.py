import os
from enum import Enum
from typing import Any, Dict, Union

from requests import Session

from smart_tests.app import Application
from smart_tests.utils.authentication import get_org_workspace
from smart_tests.utils.env_keys import CALLER_KEY, detect_ci_provider
from smart_tests.utils.http_client import _HttpClient, _join_paths
from smart_tests.version import __version__

from .commands import Command

# Map CLI subcommand tokens to Command enum values.
# Longer matches are tried first so "record build" matches before "record".
_COMMAND_MAP = {
    ("verify",): Command.VERIFY,
    ("record", "build"): Command.RECORD_BUILD,
    ("record", "session"): Command.RECORD_SESSION,
    ("record", "tests"): Command.RECORD_TESTS,
    ("record", "commit"): Command.COMMIT,
    ("record", "deployment"): Command.RECORD_DEPLOYMENT,
    ("subset",): Command.SUBSET,
    ("detect-flakes",): Command.DETECT_FLAKE,
    ("gate",): Command.GATE,
    ("update", "alias"): Command.UPDATE_ALIAS,
}


def _detect_command(argv: list[str]) -> Command:
    """Best-effort detection of the Command from argv. Returns UNKNOWN for typos."""
    args = argv[1:]
    for tokens, command in sorted(_COMMAND_MAP.items(), key=lambda x: -len(x[0])):
        for i in range(len(args) - len(tokens) + 1):
            if tuple(args[i:i + len(tokens)]) == tokens:
                return command
    return Command.UNKNOWN


def send_command_tracking(argv: list[str], exit_code: int):
    """Send a single COMMAND_INVOCATION event with the full command string. Fire-and-forget."""
    client = TrackingClient(_detect_command(argv))
    metadata = {
        "exitCode": exit_code,
    }

    payload = client.construct_payload(
        event_name=Tracking.Event.COMMAND_INVOCATION,
        metadata=metadata,
        raw_command=" ".join(argv),
    )

    client.post_payload(payload=payload)


class Tracking:
    # General events
    class Event(Enum):
        SHALLOW_CLONE = 'SHALLOW_CLONE'  # this event is an example
        PERFORMANCE = 'PERFORMANCE'
        COMMAND_INVOCATION = 'COMMAND_INVOCATION'

    # Error events
    class ErrorEvent(Enum):
        UNKNOWN_ERROR = 'UNKNOWN_ERROR'
        INTERNAL_CLI_ERROR = 'INTERNAL_CLI_ERROR'
        WARNING_ERROR = 'WARNING_ERROR'
        USER_ERROR = 'USER_ERROR'
        # Errors related to requests package
        NETWORK_ERROR = 'NETWORK_ERROR'
        TIMEOUT_ERROR = 'TIMEOUT_ERROR'
        INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR'
        UNEXPECTED_HTTP_STATUS_ERROR = 'UNEXPECTED_HTTP_STATUS_ERROR'


class TrackingClient:
    def __init__(self, command: Command, base_url: str = "", session: Session | None = None,
                 app: Application | None = None):
        self.http_client = _HttpClient(
            base_url=base_url,
            session=session,
            app=app
        )
        self.command = command

    def send_event(
        self,
        event_name: Tracking.Event,
        metadata: Dict[str, Any] | None = None
    ):
        self.post_payload(
            payload=self.construct_payload(event_name=event_name, metadata=metadata),
        )

    def send_error_event(
        self,
        event_name: Tracking.ErrorEvent,
        stack_trace: str,
        api: str = "",
        metadata: Dict[str, Any] | None = None
    ):
        if metadata is None:
            metadata = {}
        metadata["stackTrace"] = stack_trace
        metadata["api"] = api

        payload = self.construct_payload(event_name=event_name, metadata=metadata)
        self.post_payload(payload=payload)

    def post_payload(
        self,
        payload: dict,
    ):
        path = _join_paths(
            '/intake',
            'cli_tracking'
        )
        try:
            self.http_client.request('post', payload=payload, path=path)
        except Exception:
            pass

    def construct_payload(
            self,
            event_name: Union[Tracking.Event, Tracking.ErrorEvent],
            metadata: Dict[str, Any] | None = None,
            raw_command: str | None = None
    ) -> dict:
        org, workspace = get_org_workspace()

        if metadata is None:
            metadata = {}

        metadata["organization"] = org or ""
        metadata["workspace"] = workspace or ""
        metadata["caller"] = os.environ.get(CALLER_KEY) or "cli"
        metadata["ciProvider"] = detect_ci_provider()

        payload = {
            "command": self.command.value,
            "eventName": event_name.value,
            "cliVersion": __version__,
            "metadata": metadata,
            "rawCommand": raw_command or "",
        }

        return payload

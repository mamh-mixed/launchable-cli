from enum import Enum
from typing import Dict, Any, Optional, Union

from requests import Session
from launchable.utils.http_client import _HttpClient, _join_paths

from launchable.version import __version__


class Tracking:
    # General events
    class Event(Enum):
        WARNING = 'WARNING'
        SHALLOW_CLONE = 'shallow_clone'  # this event is an example

    # Error events
    class ErrorEvent(Enum):
        UNKNOWN_ERROR = 'UNKNOWN_ERROR'
        INTERNAL_CLI_ERROR = 'INTERNAL_CLI_ERROR'
        # Errors related to requests package
        NETWORK_ERROR = 'NETWORK_ERROR'
        TIMEOUT_ERROR = 'TIMEOUT_ERROR'
        INTERNAL_SERVER_ERROR = 'INTERNAL_SERVER_ERROR'
        UNEXPECTED_HTTP_STATUS_ERROR = 'UNEXPECTED_HTTP_STATUS_ERROR'

    class Command(Enum):
        VERIFY = 'VERIFY'
        RECORD_TESTS = 'RECORD_TESTS'
        RECORD_BUILD = 'RECORD_BUILD'
        RECORD_SESSION = 'RECORD_SESSION'
        SUBSET = 'SUBSET'


class TrackingClient:
    def __init__(self, command: Tracking.Command, base_url: str = "", session: Optional[Session] = None,
                 test_runner: Optional[str] = "", dry_run: bool = False):
        self.http_client = _HttpClient(
            base_url=base_url,
            session=session,
            test_runner=test_runner,
            dry_run=dry_run
        )
        self.command = command

    def send_event(
        self,
        event_name: Union[Tracking.Event, Tracking.ErrorEvent],
        organization: str = "",
        workspace: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        if metadata is None:
            metadata = {}
        metadata["organization"] = organization
        metadata["workspace"] = workspace
        self._post_payload(
            event_name=event_name,
            metadata=metadata,
        )

    def send_error_event(
        self,
        event_name: Union[Tracking.Event, Tracking.ErrorEvent],
        stack_trace: str,
        organization: str = "",
        workspace: str = "",
        api: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        if metadata is None:
            metadata = {}
        metadata["stackTrace"] = stack_trace
        metadata["organization"] = organization
        metadata["workspace"] = workspace
        metadata["api"] = api
        self._post_payload(
            event_name=event_name,
            metadata=metadata,
        )

    def _post_payload(
        self,
        event_name: Union[Tracking.Event, Tracking.ErrorEvent],
        metadata: Dict[str, Any]
    ):
        payload = {
            "command": self.command.value,
            "eventName": event_name.value,
            "cliVersion": __version__,
            "metadata": metadata,
        }
        path = _join_paths(
            '/intake',
            'cli_tracking'
        )
        try:
            self.http_client.request('post', payload=payload, path=path)
        except Exception:
            pass

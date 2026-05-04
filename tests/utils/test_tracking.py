import json
import os
from unittest import TestCase, mock

import responses

from smart_tests.utils.commands import Command
from smart_tests.utils.env_keys import detect_ci_provider
from smart_tests.utils.http_client import get_base_url
from smart_tests.utils.tracking import Tracking, TrackingClient, send_command_tracking, _detect_command


class DetectCommandTest(TestCase):

    def test_verify(self):
        self.assertEqual(_detect_command(["smart-tests", "verify"]), Command.VERIFY)

    def test_record_build(self):
        self.assertEqual(_detect_command(["smart-tests", "record", "build", "--name", "foo"]), Command.RECORD_BUILD)

    def test_record_session(self):
        self.assertEqual(_detect_command(["smart-tests", "record", "session", "--build", "123"]), Command.RECORD_SESSION)

    def test_subset(self):
        self.assertEqual(_detect_command(["smart-tests", "subset", "pytest", "--target", "30%"]), Command.SUBSET)

    def test_detect_flakes(self):
        self.assertEqual(_detect_command(["smart-tests", "detect-flakes", "pytest"]), Command.DETECT_FLAKE)

    def test_gate(self):
        self.assertEqual(_detect_command(["smart-tests", "gate", "--session", "builds/1/test_sessions/2"]), Command.GATE)

    def test_update_alias(self):
        self.assertEqual(_detect_command(["smart-tests", "update", "alias", "--build", "foo"]), Command.UPDATE_ALIAS)

    def test_typo_returns_unknown(self):
        self.assertEqual(_detect_command(["smart-tests", "recrd", "build"]), Command.UNKNOWN)

    def test_no_subcommand_returns_unknown(self):
        self.assertEqual(_detect_command(["smart-tests"]), Command.UNKNOWN)

    def test_global_options_before_command(self):
        self.assertEqual(
            _detect_command(["smart-tests", "--dry-run", "record", "build", "--name", "foo"]),
            Command.RECORD_BUILD,
        )


class DetectCiProviderTest(TestCase):

    def test_no_ci(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(detect_ci_provider(), "")

    def test_github_actions(self):
        with mock.patch.dict(os.environ, {"GITHUB_ACTIONS": "true"}, clear=True):
            self.assertEqual(detect_ci_provider(), "github-actions")

    def test_jenkins(self):
        with mock.patch.dict(os.environ, {"JENKINS_URL": "https://jenkins.example.com"}, clear=True):
            self.assertEqual(detect_ci_provider(), "jenkins")

    def test_circleci(self):
        with mock.patch.dict(os.environ, {"CIRCLECI": "true"}, clear=True):
            self.assertEqual(detect_ci_provider(), "circleci")

    def test_codebuild(self):
        with mock.patch.dict(os.environ, {"CODEBUILD_BUILD_ID": "build:123"}, clear=True):
            self.assertEqual(detect_ci_provider(), "codebuild")


class TrackingCallerTest(TestCase):

    @mock.patch.dict(
        os.environ,
        {"SMART_TESTS_TOKEN": "v1:org/ws:token"},
    )
    @responses.activate
    def test_default_caller_is_cli(self):
        responses.add(
            responses.POST,
            f"{get_base_url()}/intake/cli_tracking",
            json={},
            status=200,
        )
        client = TrackingClient(Command.VERIFY, base_url=get_base_url())
        client.send_event(Tracking.Event.PERFORMANCE, {"duration": 100})

        payload = json.loads(responses.calls[0].request.body)
        self.assertEqual(payload["metadata"]["caller"], "cli")

    @mock.patch.dict(
        os.environ,
        {
            "SMART_TESTS_TOKEN": "v1:org/ws:token",
            "SMART_TESTS_CALLER": "github-action",
        },
    )
    @responses.activate
    def test_caller_from_env(self):
        responses.add(
            responses.POST,
            f"{get_base_url()}/intake/cli_tracking",
            json={},
            status=200,
        )
        client = TrackingClient(Command.RECORD_BUILD, base_url=get_base_url())
        client.send_event(Tracking.Event.PERFORMANCE, {"duration": 100})

        payload = json.loads(responses.calls[0].request.body)
        self.assertEqual(payload["metadata"]["caller"], "github-action")

    @mock.patch.dict(
        os.environ,
        {
            "SMART_TESTS_TOKEN": "v1:org/ws:token",
            "GITHUB_ACTIONS": "true",
        },
    )
    @responses.activate
    def test_ci_provider_auto_detected(self):
        responses.add(
            responses.POST,
            f"{get_base_url()}/intake/cli_tracking",
            json={},
            status=200,
        )
        client = TrackingClient(Command.SUBSET, base_url=get_base_url())
        client.send_event(Tracking.Event.PERFORMANCE, {"duration": 100})

        payload = json.loads(responses.calls[0].request.body)
        self.assertEqual(payload["metadata"]["ciProvider"], "github-actions")
        self.assertEqual(payload["metadata"]["caller"], "cli")

    @mock.patch.dict(
        os.environ,
        {
            "SMART_TESTS_TOKEN": "v1:org/ws:token",
            "GITHUB_ACTIONS": "true",
            "SMART_TESTS_CALLER": "github-action",
        },
    )
    @responses.activate
    def test_caller_and_ci_provider_together(self):
        responses.add(
            responses.POST,
            f"{get_base_url()}/intake/cli_tracking",
            json={},
            status=200,
        )
        client = TrackingClient(Command.RECORD_BUILD, base_url=get_base_url())
        client.send_event(Tracking.Event.PERFORMANCE, {"duration": 100})

        payload = json.loads(responses.calls[0].request.body)
        self.assertEqual(payload["metadata"]["caller"], "github-action")
        self.assertEqual(payload["metadata"]["ciProvider"], "github-actions")

    @mock.patch.dict(
        os.environ,
        {"SMART_TESTS_TOKEN": "v1:org/ws:token"},
    )
    @responses.activate
    def test_error_event_includes_caller(self):
        responses.add(
            responses.POST,
            f"{get_base_url()}/intake/cli_tracking",
            json={},
            status=200,
        )
        client = TrackingClient(Command.GATE, base_url=get_base_url())
        client.send_error_event(
            event_name=Tracking.ErrorEvent.INTERNAL_CLI_ERROR,
            stack_trace="some error",
        )

        payload = json.loads(responses.calls[0].request.body)
        self.assertEqual(payload["metadata"]["caller"], "cli")
        self.assertIn("ciProvider", payload["metadata"])


class SendCommandTrackingTest(TestCase):

    @mock.patch.dict(
        os.environ,
        {"SMART_TESTS_TOKEN": "v1:org/ws:token"},
    )
    @responses.activate
    def test_sends_command_invocation(self):
        responses.add(
            responses.POST,
            f"{get_base_url()}/intake/cli_tracking",
            json={},
            status=200,
        )
        send_command_tracking(
            argv=["smart-tests", "record", "build", "--name", "foo"],
            exit_code=0,
        )

        self.assertEqual(len(responses.calls), 1)
        payload = json.loads(responses.calls[0].request.body)
        self.assertEqual(payload["command"], "RECORD_BUILD")
        self.assertEqual(payload["eventName"], "COMMAND_INVOCATION")
        self.assertEqual(payload["rawCommand"], "smart-tests record build --name foo")
        self.assertIn("cliVersion", payload)
        metadata = payload["metadata"]
        self.assertEqual(metadata["exitCode"], 0)
        self.assertEqual(metadata["caller"], "cli")

    @mock.patch.dict(
        os.environ,
        {
            "SMART_TESTS_TOKEN": "v1:org/ws:token",
            "SMART_TESTS_CALLER": "github-action",
            "GITHUB_ACTIONS": "true",
        },
    )
    @responses.activate
    def test_includes_caller_and_ci_in_metadata(self):
        responses.add(
            responses.POST,
            f"{get_base_url()}/intake/cli_tracking",
            json={},
            status=200,
        )
        send_command_tracking(argv=["smart-tests", "verify"], exit_code=0)

        payload = json.loads(responses.calls[0].request.body)
        metadata = payload["metadata"]
        self.assertEqual(metadata["caller"], "github-action")
        self.assertEqual(metadata["ciProvider"], "github-actions")

    @mock.patch.dict(
        os.environ,
        {"SMART_TESTS_TOKEN": "v1:org/ws:token"},
    )
    @responses.activate
    def test_swallows_exceptions(self):
        responses.add(
            responses.POST,
            f"{get_base_url()}/intake/cli_tracking",
            json={"error": "server error"},
            status=500,
        )
        # Should not raise
        send_command_tracking(argv=["smart-tests", "verify"], exit_code=0)

    @mock.patch.dict(
        os.environ,
        {"SMART_TESTS_TOKEN": "v1:org/ws:token"},
    )
    @responses.activate
    def test_typo_maps_to_unknown(self):
        responses.add(
            responses.POST,
            f"{get_base_url()}/intake/cli_tracking",
            json={},
            status=200,
        )
        send_command_tracking(argv=["smart-tests", "recrd", "build"], exit_code=1)

        payload = json.loads(responses.calls[0].request.body)
        self.assertEqual(payload["command"], "UNKNOWN")
        self.assertEqual(payload["metadata"]["exitCode"], 1)
        self.assertEqual(payload["rawCommand"], "smart-tests recrd build")

import json
import os
from unittest import TestCase, mock

import responses

from smart_tests.utils.commands import Command
from smart_tests.utils.http_client import get_base_url
from smart_tests.utils.env_keys import detect_ci_provider
from smart_tests.utils.tracking import Tracking, TrackingClient


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
        self.assertEqual(payload["caller"], "cli")

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
        self.assertEqual(payload["caller"], "github-action")

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
        self.assertEqual(payload["ciProvider"], "github-actions")
        # caller should still default to "cli" when wrapper hasn't set it
        self.assertEqual(payload["caller"], "cli")

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
        """The key scenario: our GitHub Action wrapper sets SMART_TESTS_CALLER
        while GITHUB_ACTIONS is auto-set by the runner."""
        responses.add(
            responses.POST,
            f"{get_base_url()}/intake/cli_tracking",
            json={},
            status=200,
        )
        client = TrackingClient(Command.RECORD_BUILD, base_url=get_base_url())
        client.send_event(Tracking.Event.PERFORMANCE, {"duration": 100})

        payload = json.loads(responses.calls[0].request.body)
        self.assertEqual(payload["caller"], "github-action")
        self.assertEqual(payload["ciProvider"], "github-actions")

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
        self.assertEqual(payload["caller"], "cli")
        self.assertIn("ciProvider", payload)

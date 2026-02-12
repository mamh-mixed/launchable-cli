import json
import os
from unittest import mock

import responses  # type: ignore

from smart_tests.utils.http_client import get_base_url
from smart_tests.utils.link import LinkKind
from tests.cli_test_case import CliTestCase


class SessionTest(CliTestCase):
    """
    This test needs to specify `clear=True` in mocking because the test is run on GithubActions.
    Otherwise GithubActions will export $GITHUB_* variables at runs.
    """

    @responses.activate
    @mock.patch.dict(os.environ, {
        "SMART_TESTS_TOKEN": CliTestCase.smart_tests_token,
        # LANG=C.UTF-8 is needed to run CliRunner().invoke(command).
        # Generally it's provided by shell. But in this case, `clear=True`
        # removes the variable.
        'LANG': 'C.UTF-8',
    }, clear=True)
    def test_run_session(self):
        result = self.cli(
            "record", "session", "--build", self.build_name,
            "--test-suite", "test-suite")
        self.assert_success(result)

        payload = json.loads(responses.calls[1].request.body.decode())
        self.assert_json_orderless_equal({
            "flavors": {},
            "isObservation": False,
            "links": [],
            "noBuild": False,
            "testSuite": "test-suite",
            "timestamp": None,
        }, payload)

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token, 'LANG': 'C.UTF-8'}, clear=True)
    def test_run_session_with_flavor(self):
        result = self.cli("record", "session", "--build", self.build_name,
                          "--test-suite", "test-suite",
                          "--flavor", "key=value", "--flavor", "k:v", "--flavor", "k e y = v a l u e")
        self.assert_success(result)

        payload = json.loads(responses.calls[1].request.body.decode())
        self.assert_json_orderless_equal({
            "flavors": {
                "key": "value",
                "k": "v",
                "k e y": "v a l u e",
            },
            "isObservation": False,
            "links": [],
            "noBuild": False,
            "testSuite": "test-suite",
            "timestamp": None,
        }, payload)

        # invalid flavor case
        result = self.cli(
            "record", "session", "--build", self.build_name,
            "--test-suite", "test-suite", "--flavor", "only-key")
        self.assert_exit_code(result, 1)
        self.assertIn("but got 'only-key'", result.output)

    @responses.activate
    @mock.patch.dict(os.environ, {
        "SMART_TESTS_TOKEN": CliTestCase.smart_tests_token,
        'LANG': 'C.UTF-8',
    }, clear=True)
    def test_run_session_with_observation(self):
        result = self.cli(
            "record", "session", "--build", self.build_name,
            "--test-suite", "test-suite", "--observation")
        self.assert_success(result)

        payload = json.loads(responses.calls[1].request.body.decode())
        self.assert_json_orderless_equal({
            "flavors": {},
            "isObservation": True,
            "links": [],
            "noBuild": False,
            "testSuite": "test-suite",
            "timestamp": None,
        }, payload)

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token, 'LANG': 'C.UTF-8'}, clear=True)
    def test_run_session_with_timestamp(self):
        result = self.cli("record", "session", "--build", self.build_name,
                          "--test-suite", "test-suite",
                          "--timestamp", "2023-10-01T12:00:00Z")
        self.assert_success(result)

        payload = json.loads(responses.calls[1].request.body.decode())
        self.assert_json_orderless_equal({
            "flavors": {},
            "isObservation": False,
            "links": [],
            "noBuild": False,
            "testSuite": "test-suite",
            "timestamp": "2023-10-01T12:00:00+00:00",
        }, payload)

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token, 'LANG': 'C.UTF-8'}, clear=True)
    def test_run_session_with_link(self):
        result = self.cli("record", "session", "--build", self.build_name,
                          "--test-suite", "test-suite",
                          "--link", "url=https://smart-tests.test")
        self.assert_success(result)

        payload = json.loads(responses.calls[1].request.body.decode())
        self.assert_json_orderless_equal({
            "flavors": {},
            "isObservation": False,
            "links": [
                {"title": "url", "url": "https://smart-tests.test", "kind": "CUSTOM_LINK"},
            ],
            "noBuild": False,
            "testSuite": "test-suite",
            "timestamp": None,
        }, payload)

    @responses.activate
    @mock.patch.dict(os.environ, {
        "LAUNCHABLE_TOKEN": CliTestCase.smart_tests_token,
        'LANG': 'C.UTF-8',
        "GITHUB_PULL_REQUEST_URL": "https://github.com/launchableinc/cli/pull/1",
    }, clear=True)
    def test_run_session_with_links(self):
        # Endpoint to assert
        endpoint = "{}/intake/organizations/{}/workspaces/{}/builds/{}/test_sessions".format(
            get_base_url(),
            self.organization,
            self.workspace,
            self.build_name)

        def invoke(*args):
            return self.cli(*("record", "session", "--build", self.build_name, "--test-suite", "test-suite") + args)

        # Capture from environment
        result = invoke()
        self.assert_success(result)
        payload = json.loads(self.find_request(endpoint, 0).request.body.decode())
        self.assertEqual([{
            "kind": LinkKind.GITHUB_PULL_REQUEST.name,
            "title": "",
            "url": "https://github.com/launchableinc/cli/pull/1",
        }], payload["links"])

        # Priority check
        result = invoke("--link", "GITHUB_PULL_REQUEST|PR=https://github.com/launchableinc/cli/pull/2")
        self.assert_success(result)
        payload = json.loads(self.find_request(endpoint, 1).request.body.decode())
        self.assertEqual([{
            "kind": LinkKind.GITHUB_PULL_REQUEST.name,
            "title": "PR",
            "url": "https://github.com/launchableinc/cli/pull/2",
        }], payload["links"])

        # Infer kind
        result = invoke("--link", "PR=https://github.com/launchableinc/cli/pull/2")
        self.assert_success(result)
        payload = json.loads(self.find_request(endpoint, 2).request.body.decode())
        self.assertEqual([{
            "kind": LinkKind.GITHUB_PULL_REQUEST.name,
            "title": "PR",
            "url": "https://github.com/launchableinc/cli/pull/2",
        }], payload["links"])

        # Explicit kind
        result = invoke("--link", "GITHUB_PULL_REQUEST|PR=https://github.com/launchableinc/cli/pull/2")
        self.assert_success(result)
        payload = json.loads(self.find_request(endpoint, 3).request.body.decode())
        self.assertEqual([{
            "kind": LinkKind.GITHUB_PULL_REQUEST.name,
            "title": "PR",
            "url": "https://github.com/launchableinc/cli/pull/2",
        }], payload["links"])

        # Multiple kinds
        result = invoke("--link", "GITHUB_ACTIONS|=https://github.com/launchableinc/mothership/actions/runs/3747451612")
        self.assert_success(result)
        payload = json.loads(self.find_request(endpoint, 4).request.body.decode())
        self.assertEqual([{
            "kind": LinkKind.GITHUB_ACTIONS.name,
            "title": "",
            "url": "https://github.com/launchableinc/mothership/actions/runs/3747451612",
        },
            {
            "kind": LinkKind.GITHUB_PULL_REQUEST.name,
            "title": "",
            "url": "https://github.com/launchableinc/cli/pull/1",
        }], payload["links"])

        # Invalid kind
        result = invoke("--link", "UNKNOWN_KIND|PR=https://github.com/launchableinc/cli/pull/2")
        self.assertIn("Invalid kind 'UNKNOWN_KIND' passed to --link option", result.output)

        # Invalid URL
        result = invoke("--link", "GITHUB_PULL_REQUEST|PR=https://github.com/launchableinc/cli/pull/2/files")
        self.assertIn("Invalid url 'https://github.com/launchableinc/cli/pull/2/files' passed to --link option", result.output)

    @responses.activate
    @mock.patch.dict(os.environ, {
        "SMART_TESTS_TOKEN": CliTestCase.smart_tests_token,
        'LANG': 'C.UTF-8',
    }, clear=True)
    def test_run_session_with_no_build(self):
        result = self.cli(
            "record", "session", "--no-build",
            "--test-suite", "test-suite")
        self.assert_success(result)

        payload = json.loads(responses.calls[1].request.body.decode())
        self.assert_json_orderless_equal({
            "flavors": {},
            "isObservation": False,
            "links": [],
            "noBuild": True,
            "testSuite": "test-suite",
            "timestamp": None,
        }, payload)

import os
from unittest import mock

import responses

from smart_tests.utils.http_client import get_base_url
from smart_tests.utils.session import SessionId, TestSession, get_session
from smart_tests.utils.smart_tests_client import SmartTestsClient
from tests.cli_test_case import CliTestCase


class TestTestSession(CliTestCase):
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    @responses.activate
    def test_get_session(self):
        client = SmartTestsClient(base_url=get_base_url())
        responses.replace(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}"
            f"/builds/{self.build_name}/test_sessions/{self.session_id}",
            json={
                'id': self.session_id,
                'buildId': 456,
                'buildNumber': self.build_name,
                'isObservation': True,
                'name': 'dummy-name',
            },
            status=200)

        test_session = get_session(SessionId(self.session), client)
        self.assertEqual(test_session, TestSession(
            id=self.session_id,
            build_id=456,
            build_name=self.build_name,
            observation_mode=True,
            name='dummy-name'))

        # not found test session case
        responses.replace(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}"
            f"/builds/{self.build_name}/test_sessions/{self.session_id}",
            json={},
            status=404)

        with self.assertRaises(SystemExit) as cm:
            get_session(SessionId(self.session), client)
        self.assertEqual(cm.exception.code, 1)

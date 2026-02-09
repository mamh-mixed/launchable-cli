import os
import tempfile
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


class TestSessionId(CliTestCase):
    """Test SessionId initialization and file reading with various encodings"""

    def setUp(self):
        super().setUp()
        # A valid session ID for testing
        self.valid_session_id = f"builds/{self.build_name}/test_sessions/{self.session_id}"

    def _assert_session_from_file(self, encoding: str, content: str):
        """Helper method to test reading session ID from a file with specific encoding"""
        with tempfile.NamedTemporaryFile(mode='w', encoding=encoding, delete=False, suffix='.txt') as f:
            f.write(content)
            temp_path = f.name

        try:
            session = SessionId(f"@{temp_path}")
            self.assertEqual(str(session), self.valid_session_id)
            self.assertEqual(session.build_part, self.build_name)
            self.assertEqual(session.test_part, self.session_id)
        finally:
            os.unlink(temp_path)

    def test_session_id_from_utf8_file_without_bom(self):
        """Test reading session ID from a UTF-8 file without BOM"""
        # also, extra NL
        self._assert_session_from_file('utf-8', f"{self.valid_session_id}\n")

    def test_session_id_from_utf8_file_with_bom(self):
        """Test reading session ID from a UTF-8 file with BOM (UTF-8 signature)"""
        self._assert_session_from_file('utf-8-sig', self.valid_session_id)

    def test_session_id_from_utf16_le_file(self):
        """Test reading session ID from a UTF-16 LE file with BOM (PowerShell default on Windows)"""
        self._assert_session_from_file('utf-16-le', f'\ufeff{self.valid_session_id}')

    def test_session_id_from_utf16_file(self):
        """Test reading session ID from a UTF-16 file with BOM (using utf-16 encoding)"""
        self._assert_session_from_file('utf-16', self.valid_session_id)

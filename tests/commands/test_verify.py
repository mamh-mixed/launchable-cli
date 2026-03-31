import os
from subprocess import CalledProcessError
from unittest import TestCase
from unittest.mock import patch

import responses  # type: ignore

from smart_tests.commands.verify import check_java_version, compare_java_version, compare_version, parse_version
from smart_tests.utils.http_client import get_base_url
from tests.cli_test_case import CliTestCase


class VersionTest(TestCase):
    def test_compare_version(self):
        def sign(x):
            if x < 0:
                return -1
            if x > 0:
                return 1
            return 0

        def f(expected, a, b):
            """Ensure symmetry on two sides"""
            self.assertEqual(sign(compare_version(a, b)), expected)
            self.assertEqual(sign(compare_version(b, a)), -expected)

        f(0, [1, 1, 0], [1, 1])     # 1.1.0 = 1.1
        f(1, [1, 1], [1, 0])        # 1.1 > 1.0
        f(1, [1, 0, 1], [1])        # 1.0.1 > 1

    def test_python_version_with_plus_sign(self):
        """Test that Python versions with '+' character are parsed correctly"""
        self.assertEqual(parse_version('3.13.0+'), [3, 13, 0])
        self.assertEqual(parse_version('3.13+'), [3, 13])
        self.assertEqual(parse_version('3.13.0'), [3, 13, 0])

    def test_java_version(self):
        self.assertTrue(compare_java_version(
            """
    java version "1.8.0_144"
    Java(TM) SE Runtime Environment (build 1.8.0_144-b01)
    Java HotSpot(TM) 64-Bit Server VM (build 25.144-b01, mixed mode)
    """
        ) >= 0)

        self.assertTrue(compare_java_version(
            """
    java version "1.5.0_22"
    Java(TM) 2 Runtime Environment, Standard Edition (build 1.5.0_22-b03)
    Java HotSpot(TM) 64-Bit Server VM (build 1.5.0_22-b03, mixed mode)
    """
        ) < 0)

    @patch('smart_tests.commands.verify.subprocess.run')
    def test_check_java_version(self, mock_run):
        mock_run.side_effect = CalledProcessError(1, 'java -version')
        result = check_java_version('java')
        self.assertEqual(result, -1)


class VerifyCommandTest(CliTestCase):
    """Test the verify command with display names"""

    @responses.activate
    @patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_verify_shows_display_name(self):
        """Test that verify displays organizationDisplayName and workspaceDisplayName from API response"""
        verification_url = f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/verification"

        # Mock server response with displayName fields
        responses.add(
            responses.GET,
            verification_url,
            json={
                "organization": self.organization,
                "organizationDisplayName": "My Company",
                "workspace": self.workspace,
                "workspaceDisplayName": "Production"
            },
            status=200
        )

        result = self.cli("verify")
        self.assert_success(result)

        # Verify displayName appears in output
        self.assertIn("'My Company'", result.output)
        self.assertIn("'Production'", result.output)

    @responses.activate
    @patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_verify_fallback_when_no_display_name(self):
        """Test that verify falls back to org/workspace when displayName not in response"""
        verification_url = f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/verification"

        # Mock server response without displayName fields
        responses.add(
            responses.GET,
            verification_url,
            json={},
            status=200
        )

        result = self.cli("verify")
        self.assert_success(result)

        # Should show original org/workspace names
        self.assertIn(f"'{self.organization}'", result.output)
        self.assertIn(f"'{self.workspace}'", result.output)

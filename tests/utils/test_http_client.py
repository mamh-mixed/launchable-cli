import os
import platform
from unittest import TestCase, mock

from smart_tests.app import Application
from smart_tests.utils.http_client import _HttpClient, _sanitize_headers
from smart_tests.version import __version__


def _clean_ci_env():
    """
    Returns env overrides that surgically clear CI-specific variables.
    Avoids clear=True which wipes the entire environment including
    SMART_TESTS_BASE_URL, causing tests to hit the production URL.
    See PR #1279 for context.
    """
    return {
        'GITHUB_ACTIONS': '',
        'GITHUB_RUN_ID': '',
        'GITHUB_REPOSITORY': '',
        'GITHUB_WORKFLOW': '',
        'GITHUB_RUN_NUMBER': '',
        'GITHUB_EVENT_NAME': '',
        'GITHUB_SHA': '',
        'GITHUB_JOB': '',
        'JENKINS_URL': '',
        'CIRCLECI': '',
        'CODEBUILD_BUILD_ID': '',
        'SMART_TESTS_CALLER': '',
    }


class HttpClientTest(TestCase):
    @mock.patch.dict(os.environ, {
        **_clean_ci_env(),
        "SMART_TESTS_ORGANIZATION": "launchableinc",
        "SMART_TESTS_WORKSPACE": "test",
        # Clear auth tokens so _headers() produces no Authorization header.
        # Without this, tokens from .envrc leak in and the full-dict assertEqual fails.
        "SMART_TESTS_TOKEN": "",
        "LAUNCHABLE_TOKEN": "",
    })
    def test_header(self):
        base_ua = f"Launchable/{__version__} (Python {platform.python_version()}, {platform.platform()})"

        cli = _HttpClient("/test")
        self.assertEqual(cli._headers(True), {
            'Content-Encoding': 'gzip',
            'Content-Type': 'application/json',
            "User-Agent": f"{base_ua} Caller/cli",
        })

        self.assertEqual(cli._headers(False), {
            'Content-Type': 'application/json',
            "User-Agent": f"{base_ua} Caller/cli",
        })

        app = Application()
        app.test_runner = "dummy"
        cli = _HttpClient("/test", app=app)
        self.assertEqual(cli._headers(False), {
            'Content-Type': 'application/json',
            "User-Agent": f"{base_ua} TestRunner/dummy Caller/cli",
        })

    @mock.patch.dict(os.environ, {
        **_clean_ci_env(),
        "SMART_TESTS_ORGANIZATION": "launchableinc",
        "SMART_TESTS_WORKSPACE": "test",
        "SMART_TESTS_CALLER": "github-action",
        "GITHUB_ACTIONS": "true",
        "GITHUB_RUN_ID": "123",
        "GITHUB_REPOSITORY": "org/repo",
        "GITHUB_WORKFLOW": "ci",
        "GITHUB_RUN_NUMBER": "1",
        "GITHUB_EVENT_NAME": "push",
        "GITHUB_SHA": "abc123",
    })
    def test_header_with_caller_and_ci(self):
        base_ua = f"Launchable/{__version__} (Python {platform.python_version()}, {platform.platform()})"

        cli = _HttpClient("/test")
        headers = cli._headers(False)
        self.assertEqual(
            headers["User-Agent"],
            f"{base_ua} Caller/github-action CI/github-actions",
        )

    @mock.patch.dict(os.environ, {
        **_clean_ci_env(),
        "SMART_TESTS_ORGANIZATION": "launchableinc",
        "SMART_TESTS_WORKSPACE": "test",
        "GITHUB_ACTIONS": "true",
        "GITHUB_RUN_ID": "123",
        "GITHUB_REPOSITORY": "org/repo",
        "GITHUB_WORKFLOW": "ci",
        "GITHUB_RUN_NUMBER": "1",
        "GITHUB_EVENT_NAME": "push",
        "GITHUB_SHA": "abc123",
    })
    def test_header_direct_cli_in_ci(self):
        """User calls CLI directly in GitHub Actions (no wrapper)."""
        base_ua = f"Launchable/{__version__} (Python {platform.python_version()}, {platform.platform()})"

        cli = _HttpClient("/test")
        headers = cli._headers(False)
        self.assertEqual(
            headers["User-Agent"],
            f"{base_ua} Caller/cli CI/github-actions",
        )

    def test_sanitize_headers_with_bearer_token(self):
        headers = {
            'Authorization': 'Bearer v1:konboi/arm-testing:cfcxxxxxxxxxxxxxx',
            'Content-Type': 'application/json',
            'User-Agent': 'test-agent'
        }
        sanitized = _sanitize_headers(headers)

        # Original headers should not be modified
        self.assertEqual(headers['Authorization'], 'Bearer v1:konboi/arm-testing:cfcxxxxxxxxxxxxxx')

        # Sanitized headers should have token redacted
        self.assertEqual(sanitized['Authorization'], 'Bearer [REDACTED]')
        self.assertEqual(sanitized['Content-Type'], 'application/json')
        self.assertEqual(sanitized['User-Agent'], 'test-agent')

    def test_sanitize_headers_without_authorization(self):
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'test-agent'
        }
        sanitized = _sanitize_headers(headers)

        # All headers should remain unchanged
        self.assertEqual(sanitized, headers)

    def test_sanitize_headers_with_non_bearer_authorization(self):
        headers = {
            'Authorization': 'Basic dXNlcjpwYXNz',
            'Content-Type': 'application/json'
        }
        sanitized = _sanitize_headers(headers)

        # Non-Bearer authorization should remain unchanged
        self.assertEqual(sanitized['Authorization'], 'Basic dXNlcjpwYXNz')

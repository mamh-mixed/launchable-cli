import os
import platform
from unittest import TestCase, mock

from smart_tests.app import Application
from smart_tests.utils.http_client import _HttpClient, _sanitize_headers
from smart_tests.version import __version__


class HttpClientTest(TestCase):
    @mock.patch.dict(
        os.environ,
        {
            "SMART_TESTS_ORGANIZATION": "launchableinc",
            "SMART_TESTS_WORKSPACE": "test",
            "SMART_TESTS_TOKEN": "",
            "LAUNCHABLE_TOKEN": "",
        },
        clear=True,
    )
    def test_header(self):
        cli = _HttpClient("/test")
        self.assertEqual(cli._headers(True), {
            'Content-Encoding': 'gzip',
            'Content-Type': 'application/json',
            "User-Agent": f"Launchable/{__version__} (Python {platform.python_version()}, {platform.platform()})",
        })

        self.assertEqual(cli._headers(False), {
            'Content-Type': 'application/json',
            "User-Agent": f"Launchable/{__version__} (Python {platform.python_version()}, {platform.platform()})",
        })

        app = Application()
        app.test_runner = "dummy"
        cli = _HttpClient("/test", app=app)
        self.assertEqual(cli._headers(False), {
            'Content-Type': 'application/json',
            "User-Agent": f"Launchable/{__version__} (Python {platform.python_version()}, "
            f"{platform.platform()}) TestRunner/dummy",
        })

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

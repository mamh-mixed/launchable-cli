import json
import os
from unittest import mock

import responses

from smart_tests.utils.http_client import get_base_url
from tests.cli_test_case import CliTestCase


class ViewTestResultsTest(CliTestCase):
    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_test_results_basic(self):
        """Test basic test results query with default parameters"""
        mock_json_response = {
            "data": {
                "results": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "testPath": "com.example.TestClass#testMethod",
                        "status": "FAILED",
                        "totalDuration": 5200,
                        "passed": 0,
                        "failed": 1,
                        "skipped": 0,
                        "session": {
                            "id": 12345,
                            "buildId": 67890,
                            "lineage": "main",
                            "createdAt": "2026-05-11T10:30:00Z"
                        },
                        "createdAt": "2026-05-11T10:30:00Z"
                    },
                    {
                        "id": "890a1234-e29b-41d4-a716-446655440001",
                        "testPath": "com.example.TestClass#testMethod2",
                        "status": "PASSED",
                        "totalDuration": 3400,
                        "passed": 1,
                        "failed": 0,
                        "skipped": 0,
                        "session": {
                            "id": 12346,
                            "buildId": 67891,
                            "lineage": "main",
                            "createdAt": "2026-05-11T11:30:00Z"
                        },
                        "createdAt": "2026-05-11T11:30:00Z"
                    }
                ]
            },
            "metadata": {
                "totalCount": 145,
                "limit": 50,
                "offset": 0,
                "hasMore": True,
                "nextOffset": 50
            }
        }

        responses.add(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/view/test-results",
            json=mock_json_response,
            status=200,
        )

        result = self.cli("view", "test-results", mix_stderr=False)
        self.assert_success(result)

        # Verify JSON output
        output_json = json.loads(result.stdout)
        self.assertEqual(len(output_json["data"]["results"]), 2)
        self.assertEqual(output_json["metadata"]["totalCount"], 145)
        self.assertTrue(output_json["metadata"]["hasMore"])

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_test_results_with_test_path(self):
        """Test test results query with test-path filter"""
        mock_json_response = {
            "data": {
                "results": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "testPath": "com.example.TestClass#testMethod",
                        "status": "FLAKE",
                        "totalDuration": 5200,
                        "passed": 1,
                        "failed": 1,
                        "skipped": 0,
                        "session": {
                            "id": 12345,
                            "buildId": 67890,
                            "lineage": "main",
                            "createdAt": "2026-05-11T10:30:00Z"
                        },
                        "createdAt": "2026-05-11T10:30:00Z"
                    }
                ]
            },
            "metadata": {
                "totalCount": 1,
                "limit": 50,
                "offset": 0,
                "hasMore": False,
                "nextOffset": 0
            }
        }

        responses.add(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/view/test-results",
            json=mock_json_response,
            status=200,
        )

        result = self.cli(
            "view", "test-results",
            "--test-path", "com.example.TestClass#testMethod",
            mix_stderr=False
        )
        self.assert_success(result)

        # Verify the request was made and query parameter was passed
        self.assertGreater(len(responses.calls), 0)
        self.assertIn("/view/test-results", responses.calls[0].request.url)
        self.assertIn("test-path=com.example.TestClass%23testMethod", responses.calls[0].request.url)

        # Verify output
        output_json = json.loads(result.stdout)
        self.assertEqual(output_json["data"]["results"][0]["testPath"], "com.example.TestClass#testMethod")

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_test_results_with_status_failed(self):
        """Test test results query with status=FAILED filter"""
        mock_json_response = {
            "data": {
                "results": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "testPath": "com.example.FailingTest#testMethod",
                        "status": "FAILED",
                        "totalDuration": 5200,
                        "passed": 0,
                        "failed": 1,
                        "skipped": 0,
                        "session": {
                            "id": 12345,
                            "buildId": 67890,
                            "lineage": "main",
                            "createdAt": "2026-05-11T10:30:00Z"
                        },
                        "createdAt": "2026-05-11T10:30:00Z"
                    }
                ]
            },
            "metadata": {
                "totalCount": 25,
                "limit": 50,
                "offset": 0,
                "hasMore": False,
                "nextOffset": 0
            }
        }

        responses.add(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/view/test-results",
            json=mock_json_response,
            status=200,
        )

        result = self.cli("view", "test-results", "--status", "FAILED", mix_stderr=False)
        self.assert_success(result)

        # Verify the query parameter was passed
        # Check request was made
        self.assertGreater(len(responses.calls), 0)
        self.assertIn("status=FAILED", responses.calls[0].request.url)

        # Verify output
        output_json = json.loads(result.stdout)
        self.assertEqual(output_json["data"]["results"][0]["status"], "FAILED")

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_test_results_with_status_passed(self):
        """Test test results query with status=PASSED filter"""
        mock_json_response = {
            "data": {
                "results": []
            },
            "metadata": {
                "totalCount": 0,
                "limit": 50,
                "offset": 0,
                "hasMore": False,
                "nextOffset": 0
            }
        }

        responses.add(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/view/test-results",
            json=mock_json_response,
            status=200,
        )

        result = self.cli("view", "test-results", "--status", "PASSED", mix_stderr=False)
        self.assert_success(result)

        # Verify the query parameter was passed
        # Check request was made
        self.assertGreater(len(responses.calls), 0)
        self.assertIn("status=PASSED", responses.calls[0].request.url)

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_test_results_with_branch(self):
        """Test test results query with branch filter"""
        mock_json_response = {
            "data": {
                "results": []
            },
            "metadata": {
                "totalCount": 0,
                "limit": 50,
                "offset": 0,
                "hasMore": False,
                "nextOffset": 0
            }
        }

        responses.add(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/view/test-results",
            json=mock_json_response,
            status=200,
        )

        result = self.cli("view", "test-results", "--branch", "develop", mix_stderr=False)
        self.assert_success(result)

        # Verify the query parameter was passed
        # Check request was made
        self.assertGreater(len(responses.calls), 0)
        self.assertIn("branch=develop", responses.calls[0].request.url)

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_test_results_with_test_suite(self):
        """Test test results query with test-suite filter"""
        mock_json_response = {
            "data": {
                "results": []
            },
            "metadata": {
                "totalCount": 0,
                "limit": 50,
                "offset": 0,
                "hasMore": False,
                "nextOffset": 0
            }
        }

        responses.add(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/view/test-results",
            json=mock_json_response,
            status=200,
        )

        result = self.cli("view", "test-results", "--test-suite", "integration-tests", mix_stderr=False)
        self.assert_success(result)

        # Verify the query parameter was passed
        # Check request was made
        self.assertGreater(len(responses.calls), 0)
        self.assertIn("test-suite=integration-tests", responses.calls[0].request.url)

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_test_results_with_date_range(self):
        """Test test results query with from/to date parameters"""
        mock_json_response = {
            "data": {
                "results": []
            },
            "metadata": {
                "totalCount": 0,
                "limit": 50,
                "offset": 0,
                "hasMore": False,
                "nextOffset": 0
            }
        }

        responses.add(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/view/test-results",
            json=mock_json_response,
            status=200,
        )

        result = self.cli(
            "view", "test-results",
            "--from", "2026-04-01",
            "--to", "2026-04-14",
            mix_stderr=False
        )
        self.assert_success(result)

        # Verify the query parameters were passed
        # Check request was made
        self.assertGreater(len(responses.calls), 0)
        self.assertIn("from=", responses.calls[0].request.url)
        self.assertIn("to=", responses.calls[0].request.url)

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_test_results_with_limit(self):
        """Test test results query with limit parameter"""
        mock_json_response = {
            "data": {
                "results": []
            },
            "metadata": {
                "totalCount": 0,
                "limit": 100,
                "offset": 0,
                "hasMore": False,
                "nextOffset": 0
            }
        }

        responses.add(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/view/test-results",
            json=mock_json_response,
            status=200,
        )

        result = self.cli("view", "test-results", "--limit", "100", mix_stderr=False)
        self.assert_success(result)

        # Verify the query parameter was passed
        # Check request was made
        self.assertGreater(len(responses.calls), 0)
        self.assertIn("limit=100", responses.calls[0].request.url)

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_test_results_with_logs(self):
        """Test test results query with logs parameter"""
        mock_json_response = {
            "data": {
                "results": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "testPath": "com.example.TestClass#testMethod",
                        "status": "FAILED",
                        "totalDuration": 5200,
                        "passed": 0,
                        "failed": 1,
                        "skipped": 0,
                        "logs": [
                            {
                                "stdout": "Test execution started\nAssertion failed",
                                "stderr": "AssertionError: Expected 5 but got 3",
                                "status": "FAILURE",
                                "createdAt": "2026-05-11T10:30:01Z"
                            }
                        ],
                        "session": {
                            "id": 12345,
                            "buildId": 67890,
                            "lineage": "main",
                            "createdAt": "2026-05-11T10:30:00Z"
                        },
                        "createdAt": "2026-05-11T10:30:00Z"
                    }
                ]
            },
            "metadata": {
                "totalCount": 1,
                "limit": 50,
                "offset": 0,
                "hasMore": False,
                "nextOffset": 0
            }
        }

        responses.add(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/view/test-results",
            json=mock_json_response,
            status=200,
        )

        result = self.cli("view", "test-results", "--logs", mix_stderr=False)
        self.assert_success(result)

        # Verify the query parameter was passed
        # Check request was made
        self.assertGreater(len(responses.calls), 0)
        self.assertIn("include-logs=true", responses.calls[0].request.url)

        # Verify logs are in output
        output_json = json.loads(result.stdout)
        self.assertIn("logs", output_json["data"]["results"][0])
        self.assertEqual(len(output_json["data"]["results"][0]["logs"]), 1)

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_test_results_with_multiple_filters(self):
        """Test test results query with multiple filters combined"""
        mock_json_response = {
            "data": {
                "results": []
            },
            "metadata": {
                "totalCount": 0,
                "limit": 50,
                "offset": 0,
                "hasMore": False,
                "nextOffset": 0
            }
        }

        responses.add(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/view/test-results",
            json=mock_json_response,
            status=200,
        )

        result = self.cli(
            "view", "test-results",
            "--status", "FAILED",
            "--branch", "main",
            "--limit", "200",
            mix_stderr=False
        )
        self.assert_success(result)

        # Verify all query parameters were passed
        # Check request was made
        self.assertGreater(len(responses.calls), 0)
        self.assertIn("status=FAILED", responses.calls[0].request.url)
        self.assertIn("branch=main", responses.calls[0].request.url)
        self.assertIn("limit=200", responses.calls[0].request.url)

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_test_results_not_found(self):
        """Test test results query when data is not found"""
        responses.add(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/view/test-results",
            json={},
            status=404,
        )

        result = self.cli("view", "test-results", mix_stderr=False)
        self.assert_exit_code(result, 1)
        self.assertIn("No test results found", result.stderr)

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_test_results_api_error(self):
        """Test test results query when API returns error"""
        responses.add(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/view/test-results",
            status=500,
        )

        result = self.cli("view", "test-results", mix_stderr=False)
        self.assert_exit_code(result, 1)
        self.assertIn("Error", result.stderr)

    def test_test_results_invalid_status(self):
        """Test test results query with invalid status value"""
        result = self.cli("view", "test-results", "--status", "INVALID", mix_stderr=False)
        self.assert_exit_code(result, 1)
        self.assertIn("Invalid status", result.stderr)
        self.assertIn("PASSED, FAILED, SKIPPED, FLAKE", result.stderr)

    def test_test_results_invalid_limit(self):
        """Test test results query with out-of-range limit"""
        result = self.cli("view", "test-results", "--limit", "600", mix_stderr=False)
        self.assert_exit_code(result, 1)
        self.assertIn("cannot be larger than 500", result.stderr)

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_test_results_empty_response(self):
        """Test test results query with empty results"""
        mock_json_response = {
            "data": {
                "results": []
            },
            "metadata": {
                "totalCount": 0,
                "limit": 50,
                "offset": 0,
                "hasMore": False,
                "nextOffset": 0
            }
        }

        responses.add(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/view/test-results",
            json=mock_json_response,
            status=200,
        )

        result = self.cli("view", "test-results", mix_stderr=False)
        self.assert_success(result)

        # Verify output contains empty results array
        output_json = json.loads(result.stdout)
        self.assertEqual(len(output_json["data"]["results"]), 0)
        self.assertEqual(output_json["metadata"]["totalCount"], 0)

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_test_results_with_offset(self):
        """Test test results query with offset parameter for pagination"""
        mock_json_response = {
            "data": {
                "results": []
            },
            "metadata": {
                "totalCount": 100,
                "limit": 50,
                "offset": 50,
                "hasMore": False,
                "nextOffset": 100
            }
        }

        responses.add(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/view/test-results",
            json=mock_json_response,
            status=200,
        )

        result = self.cli("view", "test-results", "--offset", "50", mix_stderr=False)
        self.assert_success(result)

        # Verify the request was made and query parameter was passed
        self.assertGreater(len(responses.calls), 0)
        self.assertIn("/view/test-results", responses.calls[0].request.url)
        self.assertIn("offset=50", responses.calls[0].request.url)

        # Verify output
        output_json = json.loads(result.stdout)
        self.assertEqual(output_json["metadata"]["offset"], 50)

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_test_results_with_all_statuses(self):
        """Test test results query with all different status types"""
        for status in ["PASSED", "FAILED", "SKIPPED", "FLAKE"]:
            responses.add(
                responses.GET,
                f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/view/test-results",
                json={
                    "data": {"results": []},
                    "metadata": {
                        "totalCount": 0,
                        "limit": 50,
                        "offset": 0,
                        "hasMore": False,
                        "nextOffset": 0
                    }
                },
                status=200,
            )

            result = self.cli("view", "test-results", "--status", status, mix_stderr=False)
            self.assert_success(result)

            # Verify the query parameter was passed
            self.assertGreater(len(responses.calls), 0)
            self.assertIn(f"status={status}", responses.calls[0].request.url)

            # Reset for next iteration
            responses.reset()
            responses.mock.start()

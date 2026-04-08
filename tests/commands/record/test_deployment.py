import json
import os
from unittest import mock

import responses  # type: ignore

from smart_tests.utils.http_client import get_base_url
from tests.cli_test_case import CliTestCase


class DeploymentTest(CliTestCase):
    environment = "staging"
    service = "payment"
    build_name = "jenkins-main-135"
    error_body = "Build 'jenkins-main-135' not found"

    def deployment_url(self):
        alias_name = f"deployment:{self.environment}:{self.service}"
        return (
            f"{get_base_url()}/intake/organizations/{self.organization}"
            f"/workspaces/{self.workspace}/builds/aliases/{alias_name}"
        )

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_record_deployment(self):
        responses.add(responses.PUT, self.deployment_url(), json={}, status=200)

        result = self.cli(
            "record", "deployment",
            "--build", self.build_name,
            "--environment", self.environment,
            "--service", self.service,
        )
        self.assert_success(result)

        put_call = next(c for c in responses.calls if c.request.method == "PUT")
        self.assert_json_orderless_equal(
            {"build": self.build_name},
            json.loads(put_call.request.body)
        )
        self.assertIn(self.service, result.output)
        self.assertIn(self.environment, result.output)
        self.assertIn(self.build_name, result.output)

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_record_deployment_build_not_found(self):
        """Without fail-fast mode: prints warning in yellow, exits 0 (doesn't halt CI)."""
        responses.add(responses.PUT, self.deployment_url(), json={"reason": self.error_body}, status=404)

        result = self.cli(
            "record", "deployment",
            "--build", self.build_name,
            "--environment", self.environment,
            "--service", self.service,
        )
        self.assert_success(result)
        self.assertIn(self.error_body, result.output)

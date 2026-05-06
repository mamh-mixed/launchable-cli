import json
import os
from unittest import mock

import responses  # type: ignore

from smart_tests.utils.http_client import get_base_url
from tests.cli_test_case import CliTestCase


class AliasTest(CliTestCase):
    alias_name = "staging-payment-svc"
    build_name_target = "jenkins-main-135"
    error_body = "Build 'jenkins-main-135' not found"

    def alias_url(self):
        return (
            f"{get_base_url()}/intake/organizations/{self.organization}"
            f"/workspaces/{self.workspace}/builds/aliases/{self.alias_name}"
        )

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_update_alias(self):
        responses.add(responses.PUT, self.alias_url(), json={}, status=200)

        result = self.cli(
            "update", "alias",
            "--build", self.build_name_target,
            "--alias", self.alias_name,
        )
        self.assert_success(result)

        put_call = next(c for c in responses.calls if c.request.method == "PUT")
        self.assert_json_orderless_equal(
            {"build": self.build_name_target},
            json.loads(put_call.request.body)
        )
        self.assertIn(self.alias_name, result.output)
        self.assertIn(self.build_name_target, result.output)

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_update_alias_build_not_found(self):
        """Without fail-fast mode: prints warning in yellow, exits 0 (doesn't halt CI)."""
        responses.add(responses.PUT, self.alias_url(), json={"reason": self.error_body}, status=404)

        result = self.cli(
            "update", "alias",
            "--build", self.build_name_target,
            "--alias", self.alias_name,
        )
        self.assert_success(result)
        self.assertIn(self.error_body, result.output)

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    @mock.patch("smart_tests.utils.fail_fast_mode.is_fail_fast_mode", return_value=True)
    def test_update_alias_build_not_found_fail_fast(self, _mock_ffm):
        """With fail-fast mode: prints error in red, exits 1."""
        responses.add(responses.PUT, self.alias_url(), json={"reason": self.error_body}, status=404)

        result = self.cli(
            "update", "alias",
            "--build", self.build_name_target,
            "--alias", self.alias_name,
        )
        self.assert_exit_code(result, 1)
        self.assertIn(self.error_body, result.output)

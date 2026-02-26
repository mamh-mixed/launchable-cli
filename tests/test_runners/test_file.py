import os
from unittest import mock

import responses  # type: ignore

from tests.cli_test_case import CliTestCase


class FileTest(CliTestCase):
    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_record_test_file(self):
        result = self.cli(
            "record",
            "tests",
            "--session",
            self.session,
            "file",
            str(self.test_files_dir.joinpath("result.xml")),
        )

        self.assert_success(result)
        self.assert_record_tests_payload("record_test_result.json")

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_record_test_file_with_custom_file_path_attribute(self):
        """Test that --file-path-attribute option allows specifying custom attributes"""
        result = self.cli(
            "record",
            "tests",
            "--session",
            self.session,
            "file",
            "--file-path-attribute",
            "name",
            str(self.test_files_dir.joinpath("result_custom_attribute.xml")),
        )

        self.assert_success(result)
        self.assert_record_tests_payload("record_test_result_custom_attribute.json")

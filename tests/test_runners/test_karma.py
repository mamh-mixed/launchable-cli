import os
from unittest import mock

import responses  # type: ignore

from tests.cli_test_case import CliTestCase


class KarmaTest(CliTestCase):
    @responses.activate
    @mock.patch.dict(os.environ,
                     {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_record_tests_json(self):
        result = self.cli('record', 'tests', '--session', self.session,
                          'karma', str(self.test_files_dir.joinpath("sample-report.json")))

        self.assert_success(result)
        self.assert_record_tests_payload('record_test_result.json')

    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_subset(self):
        result = self.cli('subset', 'karma', '--session', self.session, '--target', '10%', '--base',
                          os.getcwd(), '--with', 'ng', input="a.ts\nb.ts")
        self.assert_success(result)
        self.assert_subset_payload('subset_result.json')

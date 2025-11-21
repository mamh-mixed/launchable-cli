import os
from unittest import mock

import responses  # type: ignore

from tests.cli_test_case import CliTestCase


class KarmaTest(CliTestCase):
    @responses.activate
    @mock.patch.dict(os.environ,
                     {"LAUNCHABLE_TOKEN": CliTestCase.launchable_token})
    def test_record_tests_json(self):
        result = self.cli('record', 'tests', '--session', self.session,
                          'karma', str(self.test_files_dir.joinpath("sample-report.json")))

        self.assert_success(result)
        self.assert_record_tests_payload('record_test_result.json')

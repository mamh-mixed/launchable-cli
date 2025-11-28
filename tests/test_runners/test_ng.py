import os
from unittest import mock

import responses  # type: ignore

from tests.cli_test_case import CliTestCase


class NgTest(CliTestCase):
    @responses.activate
    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_subset(self):
        subset_input = """foo/bar/zot.spec.ts
client-source/src/app/shared/other-test.spec.ts
"""
        result = self.cli('subset', 'ng', '--session', self.session, '--target', '10%', input=subset_input)
        self.assert_success(result)
        self.assert_subset_payload('subset_payload.json')

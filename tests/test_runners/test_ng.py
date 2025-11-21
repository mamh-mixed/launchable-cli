import os
from unittest import mock

import responses  # type: ignore

from launchable.utils.session import write_build
from tests.cli_test_case import CliTestCase


class NgTest(CliTestCase):
    @responses.activate
    @mock.patch.dict(os.environ,
                     {"LAUNCHABLE_TOKEN": CliTestCase.launchable_token})
    def test_subset(self):
        write_build(self.build_name)

        subset_input = """foo/bar/zot.spec.ts
client-source/src/app/shared/other-test.spec.ts
"""
        result = self.cli('subset', '--target', '10%', 'ng', input=subset_input)
        self.assert_success(result)
        self.assert_subset_payload('subset_payload.json')

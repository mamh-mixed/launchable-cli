#
# The most bare-bone versions of the test runner support
#

from junitparser import TestCase, TestSuite  # type: ignore

from . import smart_tests
from ..commands.subset import Subset


@smart_tests.subset
def subset(client: Subset):
    # read lines as test file names
    for t in client.stdin():
        client.test_path(t.rstrip("\n"))

    client.run()


record_tests = smart_tests.CommonRecordTestImpls(__name__).file_profile_report_files()
smart_tests.CommonDetectFlakesImpls(__name__).detect_flakes()
# split_subset = launchable.CommonSplitSubsetImpls(__name__).split_subset()

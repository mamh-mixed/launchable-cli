#
# The most bare-bone versions of the test runner support
#

from . import smart_tests

subset = smart_tests.CommonSubsetImpls(__name__).scan_stdin()
record_tests = smart_tests.CommonRecordTestImpls(__name__).file_profile_report_files()
smart_tests.CommonDetectFlakesImpls(__name__).detect_flakes()
# split_subset = launchable.CommonSplitSubsetImpls(__name__).split_subset()

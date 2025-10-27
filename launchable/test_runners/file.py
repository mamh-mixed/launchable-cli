#
# The most bare-bone versions of the test runner support
#

from . import launchable


@launchable.subset
def subset(client):
    # read lines as test file names
    for t in client.stdin():
        client.test_path(t.rstrip("\n"))

    client.run()


record_tests = launchable.CommonRecordTestImpls(__name__).file_profile_report_files()

split_subset = launchable.CommonSplitSubsetImpls(__name__).split_subset()

launchable.CommonFlakeDetectionImpls(__name__).detect_flakes()

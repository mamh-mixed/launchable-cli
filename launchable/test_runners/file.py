#
# The most bare-bone versions of the test runner support
#
import click

from . import launchable


@launchable.subset
def subset(client):
    # read lines as test file names
    for t in client.stdin():
        client.test_path(t.rstrip("\n"))

    client.run()


@click.argument('reports', required=True, nargs=-1)
@launchable.record.tests
def record_tests(client, reports):
    client.path_builder = launchable.CommonRecordTestImpls.create_file_path_builder(
        client
    )

    for r in reports:
        client.report(r)
    client.run()


split_subset = launchable.CommonSplitSubsetImpls(__name__).split_subset()

launchable.CommonFlakeDetectionImpls(__name__).detect_flakes()

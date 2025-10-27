import json
from typing import List

import click

from ..testpath import TestPath
from . import launchable


@launchable.subset
def subset(client):
    def handler(output: List[TestPath], rests: List[TestPath]):
        # The output would be something like this:
        # {"tests": ["test/example_test.js", "test/login_test.js"]}
        if client.rest:
            with open(client.rest, "w+", encoding="utf-8") as f:
                f.write(json.dumps({"tests": [client.formatter(t) for t in rests]}))
        if output:
            click.echo(json.dumps({"tests": [client.formatter(t) for t in output]}))

    # read lines as test file names
    for t in client.stdin():
        client.test_path(t.rstrip("\n"))
    client.output_handler = handler

    client.run()


@click.argument("reports", required=True, nargs=-1)
@launchable.record.tests
def record_tests(client, reports):
    client.path_builder = launchable.CommonRecordTestImpls.create_file_path_builder(
        client
    )

    for r in reports:
        client.report(r)
    client.run()


split_subset = launchable.CommonSplitSubsetImpls(__name__).split_subset()

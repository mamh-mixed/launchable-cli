import importlib
import importlib.util
import sys
from glob import glob
from os.path import basename, dirname, join

from smart_tests.app import Application
from smart_tests.args4p.command import Group
from smart_tests.commands.compare import compare
from smart_tests.commands.detect_flakes import detect_flakes
from smart_tests.commands.inspect import inspect
from smart_tests.commands.record import record
from smart_tests.commands.stats import stats
from smart_tests.commands.subset import subset
from smart_tests.commands.verify import verify

cli = Group(name="cli", callback=Application)
cli.add_command(record)
cli.add_command(subset)
# TODO: main.add_command(split_subset)
cli.add_command(verify)
cli.add_command(inspect)
cli.add_command(stats)
cli.add_command(compare)
cli.add_command(detect_flakes)


def _load_test_runners():
    # load all test runners
    for f in glob(join(dirname(__file__), 'test_runners', "*.py")):
        f = basename(f)[:-3]
        if f == '__init__':
            continue
        importlib.import_module(f'smart_tests.test_runners.{f}')

    # load all plugins. Here we do a bit of command line parsing ourselves,
    # because the command line could look something like `smart-tests record tests myprofile --plugins ...
    plugin_dir = None
    if "--plugins" in sys.argv:
        idx = sys.argv.index("--plugins")
        if idx + 1 < len(sys.argv):
            plugin_dir = sys.argv[idx + 1]

    if plugin_dir:
        for f in glob(join(plugin_dir, '*.py')):
            spec = importlib.util.spec_from_file_location(
                f"smart_tests.plugins.{basename(f)[:-3]}", f)
            plugin = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(plugin)


_load_test_runners()


def main():
    cli.main()


if __name__ == '__main__':
    main()

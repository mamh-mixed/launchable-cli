import importlib.resources
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import click

from ... import args4p
from ...app import Application

DOCSITE_REPO = 'git@github.com:cloudbees/docsite-cloudbees-smart-tests.git'
OUTPUT_DIR = 'smart-tests-docs'


def _find_bundled_docs() -> Path | None:
    """Return the path to the bundled docs/ directory, or None if not present."""
    pkg = importlib.resources.files('smart_tests') / 'docs'
    # files() returns a Traversable; check it's a real, non-empty directory
    try:
        p = Path(str(pkg))
        if p.is_dir() and any(p.iterdir()):
            return p
    except (TypeError, OSError):
        pass
    return None


def _fetch_docs_via_git() -> Path:
    """
    Clone the docsite repo into smart_tests/docs/ (relative to this package's
    location) and return the path to the docs/ subdirectory.

    If smart_tests/docs/ already exists, run `git pull` instead of cloning.
    """
    package_dir = Path(__file__).parent.parent.parent  # smart_tests/
    docs_dst = package_dir / 'docs'

    if docs_dst.is_dir():
        click.echo(f"Updating docs from {DOCSITE_REPO} ...")
        subprocess.run(['git', '-C', str(docs_dst), 'pull'], check=True)
    else:
        click.echo(f"Cloning docs from {DOCSITE_REPO} ...")
        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                ['git', 'clone', '--depth=1', DOCSITE_REPO, tmpdir],
                check=True,
            )
            shutil.copytree(Path(tmpdir) / 'docs', docs_dst)

    return docs_dst


@args4p.command(help="Copy product documentation into ./smart-tests-docs")
def docs(app: Application):
    output = Path(OUTPUT_DIR)
    if output.exists():
        click.secho(
            f"'{OUTPUT_DIR}' already exists. Please delete it first, then re-run this command.",
            fg='red', err=True,
        )
        sys.exit(1)

    docs_src = _find_bundled_docs()
    if docs_src is None:
        # Dev mode: not running from an installed package
        docs_src = _fetch_docs_via_git()

    click.echo(f"Copying docs to ./{OUTPUT_DIR} ...")
    shutil.copytree(docs_src, output)
    click.echo(f"Done. Documentation is in ./{OUTPUT_DIR}")

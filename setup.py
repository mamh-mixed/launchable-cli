import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py

_DOCSITE_REPO = 'git@github.com:cloudbees/docsite-cloudbees-smart-tests.git'


class BuildPyWithDocs(build_py):
    def run(self):
        docs_dst = Path(__file__).parent / 'smart_tests' / 'docs'
        if docs_dst.exists():
            shutil.rmtree(docs_dst)

        # In CI, actions/checkout pre-checks out the docsite and sets this variable
        # so we never need to handle auth here. Fall back to git clone for local dev.
        precheck = os.environ.get('DOCSITE_DOCS_PATH')
        if precheck:
            shutil.copytree(Path(precheck), docs_dst)
        else:
            with tempfile.TemporaryDirectory() as tmpdir:
                subprocess.run(
                    ['git', 'clone', '--depth=1', _DOCSITE_REPO, tmpdir],
                    check=True,
                )
                shutil.copytree(Path(tmpdir) / 'docs', docs_dst)

        super().run()


setup(cmdclass={'build_py': BuildPyWithDocs})

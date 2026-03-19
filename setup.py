import shutil
import subprocess
import tempfile
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildPyWithDocs(build_py):
    def run(self):
        docs_dst = Path(__file__).parent / 'smart_tests' / 'docs'
        if docs_dst.exists():
            shutil.rmtree(docs_dst)

        with tempfile.TemporaryDirectory() as tmpdir:
            subprocess.run(
                ['git', 'clone', '--depth=1',
                 'git@github.com:cloudbees/docsite-cloudbees-smart-tests.git', tmpdir],
                check=True,
            )
            shutil.copytree(Path(tmpdir) / 'docs', docs_dst)

        super().run()


setup(cmdclass={'build_py': BuildPyWithDocs})

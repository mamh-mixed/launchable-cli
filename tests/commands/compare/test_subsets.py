import os
from unittest import mock

import responses

from smart_tests.utils.http_client import get_base_url
from tests.cli_test_case import CliTestCase


class SubsetsTest(CliTestCase):

    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_subsets(self):
        # Create subset-before.txt
        with open("subset-before.txt", "w") as f:
            f.write("\n".join([
                "src/test/java/example/DivTest.java",
                "src/test/java/example/DB1Test.java",
                "src/test/java/example/MulTest.java",
                "src/test/java/example/Add2Test.java",
                "src/test/java/example/File1Test.java",
                "src/test/java/example/File0Test.java",
                "src/test/java/example/SubTest.java",
                "src/test/java/example/DB0Test.java",
                "src/test/java/example/AddTest.java",
            ]))

        # Create subset-after.txt
        with open("subset-after.txt", "w") as f:
            f.write("\n".join([
                "src/test/java/example/Add2Test.java",
                "src/test/java/example/MulTest.java",
                "src/test/java/example/AddTest.java",
                "src/test/java/example/File1Test.java",
                "src/test/java/example/DivTest.java",
                "src/test/java/example/File0Test.java",
                "src/test/java/example/DB1Test.java",
                "src/test/java/example/DB0Test.java",
                "src/test/java/example/SubTest.java",
            ]))

        result = self.cli('compare', 'subsets', "subset-before.txt", "subset-after.txt", mix_stderr=False)
        expect = """|   Before |   After |   After - Before | Test                                 |
|----------|---------|------------------|--------------------------------------|
|        9 |       3 |               -6 | src/test/java/example/AddTest.java   |
|        4 |       1 |               -3 | src/test/java/example/Add2Test.java  |
|        3 |       2 |               -1 | src/test/java/example/MulTest.java   |
|        5 |       4 |               -1 | src/test/java/example/File1Test.java |
|        6 |       6 |               +0 | src/test/java/example/File0Test.java |
|        8 |       8 |               +0 | src/test/java/example/DB0Test.java   |
|        7 |       9 |               +2 | src/test/java/example/SubTest.java   |
|        1 |       5 |               +4 | src/test/java/example/DivTest.java   |
|        2 |       7 |               +5 | src/test/java/example/DB1Test.java   |
"""

        self.assertEqual(result.stdout, expect)

    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_subsets_when_new_tests(self):
        # Create subset-before.txt
        with open("subset-before.txt", "w") as f:
            f.write("\n".join([
                "src/test/java/example/SubTest.java",
                "src/test/java/example/DivTest.java",
                "src/test/java/example/Add2Test.java",
                "src/test/java/example/File0Test.java",
                "src/test/java/example/AddTest.java",
                "src/test/java/example/File1Test.java",
                "src/test/java/example/MulTest.java",
                "src/test/java/example/DB0Test.java",
                "src/test/java/example/DB1Test.java"
            ]))

        # Create subset-after.txt (which includes additional test path NewTest.java)
        with open("subset-after.txt", "w") as f:
            f.write("\n".join([
                "src/test/java/example/NewTest.java",
                "src/test/java/example/SubTest.java",
                "src/test/java/example/File0Test.java",
                "src/test/java/example/DB1Test.java",
                "src/test/java/example/DivTest.java",
                "src/test/java/example/MulTest.java",
                "src/test/java/example/File1Test.java",
                "src/test/java/example/DB0Test.java",
                "src/test/java/example/Add2Test.java",
                "src/test/java/example/AddTest.java"
            ]))

        result = self.cli('compare', 'subsets', "subset-before.txt", "subset-after.txt", mix_stderr=False)
        expect = """| Before   |   After | After - Before   | Test                                 |
|----------|---------|------------------|--------------------------------------|
| -        |       1 | NEW              | src/test/java/example/NewTest.java   |
| 9        |       4 | -5               | src/test/java/example/DB1Test.java   |
| 4        |       3 | -1               | src/test/java/example/File0Test.java |
| 7        |       6 | -1               | src/test/java/example/MulTest.java   |
| 8        |       8 | +0               | src/test/java/example/DB0Test.java   |
| 1        |       2 | +1               | src/test/java/example/SubTest.java   |
| 6        |       7 | +1               | src/test/java/example/File1Test.java |
| 2        |       5 | +3               | src/test/java/example/DivTest.java   |
| 5        |      10 | +5               | src/test/java/example/AddTest.java   |
| 3        |       9 | +6               | src/test/java/example/Add2Test.java  |
"""

        self.assertEqual(result.stdout, expect)

    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    def test_subsets_when_deleted_tests(self):
        # Create subset-before.txt
        with open("subset-before.txt", "w") as f:
            f.write("\n".join([
                "src/test/java/example/NewTest.java",
                "src/test/java/example/SubTest.java",
                "src/test/java/example/File0Test.java",
                "src/test/java/example/DB1Test.java",
                "src/test/java/example/DivTest.java",
                "src/test/java/example/MulTest.java",
                "src/test/java/example/File1Test.java",
                "src/test/java/example/DB0Test.java",
                "src/test/java/example/Add2Test.java",
                "src/test/java/example/AddTest.java"
            ]))

        # Create subset-after.txt (which doesn't include NewTest.java)
        with open("subset-after.txt", "w") as f:
            f.write("\n".join([
                "src/test/java/example/DB1Test.java",
                "src/test/java/example/DB0Test.java",
                "src/test/java/example/File1Test.java",
                "src/test/java/example/SubTest.java",
                "src/test/java/example/AddTest.java",
                "src/test/java/example/MulTest.java",
                "src/test/java/example/File0Test.java",
                "src/test/java/example/Add2Test.java",
                "src/test/java/example/DivTest.java"
            ]))

        result = self.cli('compare', 'subsets', "subset-before.txt", "subset-after.txt", mix_stderr=False)
        expect = """|   Before | After   | After - Before   | Test                                 |
|----------|---------|------------------|--------------------------------------|
|        1 | -       | DELETED          | src/test/java/example/NewTest.java   |
|        8 | 2       | -6               | src/test/java/example/DB0Test.java   |
|       10 | 5       | -5               | src/test/java/example/AddTest.java   |
|        7 | 3       | -4               | src/test/java/example/File1Test.java |
|        4 | 1       | -3               | src/test/java/example/DB1Test.java   |
|        9 | 8       | -1               | src/test/java/example/Add2Test.java  |
|        6 | 6       | +0               | src/test/java/example/MulTest.java   |
|        2 | 4       | +2               | src/test/java/example/SubTest.java   |
|        3 | 7       | +4               | src/test/java/example/File0Test.java |
|        5 | 9       | +4               | src/test/java/example/DivTest.java   |
"""

        self.assertEqual(result.stdout, expect)

    def tearDown(self):
        if os.path.exists("subset-before.txt"):
            os.remove("subset-before.txt")
        if os.path.exists("subset-after.txt"):
            os.remove("subset-after.txt")

    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    @responses.activate
    def test_subsets_subset_ids(self):
        responses.add(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/subset/100",
            json={
                "subsetting": {
                    "id": 100,
                },
                "testPaths": [
                    {"testPath": [{"type": "file", "name": "aaa.py"}], "duration": 10, "density": 0.9, "reason": "Changed file: aaa.py"},  # noqa: E501
                    {"testPath": [{"type": "file", "name": "bbb.py"}], "duration": 10, "density": 0.8, "reason": "Changed file: bbb.py"}  # noqa: E501
                ],
                "rest": [
                    {"testPath": [{"type": "file", "name": "ccc.py"}], "duration": 10, "density": 0.7, "reason": "Changed file: ccc.py"}  # noqa: E501
                ]
            },
            status=200
        )
        responses.add(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/subset/101",
            json={
                "subsetting": {
                    "id": 101,
                },
                "testPaths": [
                    {"testPath": [{"type": "file", "name": "ddd.py"}], "duration": 10, "density": 0.9, "reason": "Changed file: ddd.py"},  # noqa: E501
                    {"testPath": [{"type": "file", "name": "ccc.py"}], "duration": 10, "density": 0.7, "reason": "Changed file: ccc.py"}  # noqa: E501
                ],
                "rest": [
                    {"testPath": [{"type": "file", "name": "bbb.py"}], "duration": 10, "density": 0.5, "reason": "Changed file: bbb.py"}   # noqa: E501
                ]
            },
            status=200
        )

        result = self.cli('compare', 'subsets',
                          '--subset-id-before', '100',
                          '--subset-id-after', '101',
                          mix_stderr=False)

        self.assert_success(result)
        output = result.stdout
        self.assertIn("3 tests analyzed | 1 ↑ promoted | 1 ↓ demoted", output)
        self.assertIn("Code files affected: bbb.py, ccc.py, ddd.py", output)
        self.assertIn("Δ Rank", output)
        self.assertIn("Density", output)
        for expected_row in [
            ("NEW", "1", "file=ddd.py", "Changed file: ddd.py", "0.9"),
            ("↑1", "2", "file=ccc.py", "Changed file: ccc.py", "0.7"),
            ("↓1", "3", "file=bbb.py", "Changed file: bbb.py", "0.5"),
            ("DELETED", "-", "file=aaa.py"),
        ]:
            for cell in expected_row:
                self.assertIn(cell, output)

    def test_wrap_data(self):
        """Test that wrap_data breaks paths at separators."""
        from smart_tests.commands.compare.subsets import wrap_data

        # Short path - no wrapping needed
        short = "Changed file: aaa.py"
        self.assertEqual(wrap_data(short, width=30), short)

        # Empty string
        self.assertEqual(wrap_data("", width=30), "")

        # Long path - should wrap at /
        long_path = "Changed file: src/mongo/db/telemetry/telemetry_thread_base.cpp"
        wrapped = wrap_data(long_path, width=30)

        # Verify it contains newlines
        self.assertIn("\n", wrapped)

        # Verify no unwanted spaces around path separators
        self.assertNotIn(" /", wrapped)

        # Verify content is preserved (just reformatted)
        unwrapped = wrapped.replace("\n", "")
        self.assertEqual(unwrapped, long_path)

        # Windows path test
        windows_path = "Changed file: C:\\Users\\test\\very\\long\\windows\\path\\file.cpp"
        wrapped_win = wrap_data(windows_path, width=30)
        self.assertIn("\n", wrapped_win)
        self.assertNotIn(" \\", wrapped_win)

        # Verify content preservation
        self.assertEqual(wrapped_win.replace("\n", ""), windows_path)

    def test_get_column_width(self):
        """Test that get_column_width() calculates widths based on terminal size."""
        from smart_tests.commands.compare.subsets import get_column_width

        # Test with a wide terminal (e.g., 160 columns)
        # Available width = 160 - 36 (fixed columns) = 124
        # Per column = 124 / 2 = 62
        with mock.patch("shutil.get_terminal_size") as mock_terminal:
            mock_terminal.return_value = os.terminal_size((160, 24))
            width = get_column_width()
            self.assertEqual(width, 62)

        # Test with standard terminal (80 columns)
        # Available width = 80 - 36 = 44
        # Per column = 44 / 2 = 22, but minimum is 30
        with mock.patch("shutil.get_terminal_size") as mock_terminal:
            mock_terminal.return_value = os.terminal_size((80, 24))
            width = get_column_width()
            self.assertEqual(width, 30)  # Should hit minimum

        # Test with narrow terminal (60 columns)
        # Should still return minimum of 30
        with mock.patch("shutil.get_terminal_size") as mock_terminal:
            mock_terminal.return_value = os.terminal_size((60, 24))
            width = get_column_width()
            self.assertEqual(width, 30)  # Should hit minimum

        # Test with very wide terminal (200 columns)
        # Available width = 200 - 36 = 164
        # Per column = 164 / 2 = 82
        with mock.patch("shutil.get_terminal_size") as mock_terminal:
            mock_terminal.return_value = os.terminal_size((200, 24))
            width = get_column_width()
            self.assertEqual(width, 82)

        # Test fallback when get_terminal_size raises exception
        with mock.patch("shutil.get_terminal_size") as mock_terminal:
            mock_terminal.side_effect = Exception("Terminal size unavailable")
            width = get_column_width()
            self.assertEqual(width, 30)  # Should fall back to default

    @mock.patch.dict(os.environ, {"SMART_TESTS_TOKEN": CliTestCase.smart_tests_token})
    @responses.activate
    @mock.patch('shutil.get_terminal_size', return_value=os.terminal_size((80, 24)))
    def test_subsets_with_long_paths_wrapped(self, mock_terminal_size):
        """Test that long file paths in Reason column are wrapped properly."""
        long_path1 = "src/mongo/db/telemetry/telemetry_thread_base.cpp"
        long_path2 = "jstests/concurrency/fsm_workloads/timeseries/timeseries_raw_data_operations.js"

        responses.add(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/subset/200",
            json={
                "subsetting": {"id": 200},
                "testPaths": [
                    {"testPath": [{"type": "file", "name": long_path1}],
                     "duration": 10, "density": 0.9,
                     "reason": f"Changed file: {long_path1}"}
                ],
                "rest": []
            },
            status=200
        )

        responses.add(
            responses.GET,
            f"{get_base_url()}/intake/organizations/{self.organization}/workspaces/{self.workspace}/subset/201",
            json={
                "subsetting": {"id": 201},
                "testPaths": [
                    {"testPath": [{"type": "file", "name": long_path2}],
                     "duration": 10, "density": 0.85,
                     "reason": f"Changed file: {long_path2}"}
                ],
                "rest": []
            },
            status=200
        )

        result = self.cli('compare', 'subsets',
                          '--subset-id-before', '200',
                          '--subset-id-after', '201',
                          mix_stderr=False)

        self.assert_success(result)

        # Verify output contains the summary
        self.assertIn("PTS subset change summary:", result.stdout)
        self.assertIn("Changed file:", result.stdout)

        # Verify the long paths are present (even if wrapped)
        self.assertIn("telemetry_thread_base.cpp", result.stdout)
        self.assertIn("timeseries_raw_data_operations.js", result.stdout)

        # Verify no line has excessive length (wrapped properly)
        for line in result.stdout.split('\n'):
            # Allow some buffer for separator lines
            if line.strip() and not line.startswith('─'):
                self.assertLessEqual(len(line), 150)

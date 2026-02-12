import tempfile
from pathlib import Path
from unittest import TestCase

from smart_tests.args4p.converters import fileText, floatType, intType, path


class PathConverterTest(TestCase):
    def test_path_basic(self):
        """Test basic path conversion"""
        converter = path()
        result = converter("/tmp/test")
        self.assertIsInstance(result, Path)
        self.assertEqual(result, Path("/tmp/test"))

    def test_path_resolve(self):
        """Test path resolution"""
        converter = path(resolve_path=True)
        result = converter(".")
        self.assertIsInstance(result, Path)
        self.assertTrue(result.is_absolute())

    def test_path_exists_validation(self):
        """Test that exists=True raises error for non-existent paths"""
        with tempfile.TemporaryDirectory() as tmpdir:
            converter = path(exists=True)

            # Should work for existing path
            result = converter(tmpdir)
            self.assertEqual(result, Path(tmpdir))

            # Should fail for non-existent path
            with self.assertRaises(ValueError) as ctx:
                converter(f"{tmpdir}/nonexistent")
            self.assertIn("does not exist", str(ctx.exception))

    def test_path_file_okay_validation(self):
        """Test file_okay validation"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
            try:
                converter = path(exists=True, file_okay=False)

                with self.assertRaises(ValueError) as ctx:
                    converter(tmp_path)
                self.assertIn("is a file", str(ctx.exception))
                self.assertIn("directory is expected", str(ctx.exception))
            finally:
                # On Windows, somehow we can't delete the file, so we skip it.
                # Path(tmp_path).unlink()
                pass

    def test_path_dir_okay_validation(self):
        """Test dir_okay validation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            converter = path(exists=True, dir_okay=False)

            with self.assertRaises(ValueError) as ctx:
                converter(tmpdir)
            self.assertIn("is a directory", str(ctx.exception))
            self.assertIn("file is expected", str(ctx.exception))


class FloatTypeConverterTest(TestCase):
    def test_float_basic(self):
        """Test basic float conversion"""
        converter = floatType()
        self.assertEqual(converter("3.14"), 3.14)
        self.assertEqual(converter("42"), 42.0)
        self.assertEqual(converter("-1.5"), -1.5)

    def test_float_invalid(self):
        """Test float conversion with invalid input"""
        converter = floatType()

        with self.assertRaises(ValueError) as ctx:
            converter("not_a_number")
        self.assertIn("is not a valid float", str(ctx.exception))

    def test_float_min_validation(self):
        """Test float minimum validation"""
        converter = floatType(min=0.0)

        # Should work for valid values
        self.assertEqual(converter("0.0"), 0.0)
        self.assertEqual(converter("1.5"), 1.5)

        # Should fail for values below minimum
        with self.assertRaises(ValueError) as ctx:
            converter("-1.0")
        self.assertIn("cannot be smaller than", str(ctx.exception))

    def test_float_max_validation(self):
        """Test float maximum validation"""
        converter = floatType(max=100.0)

        # Should work for valid values
        self.assertEqual(converter("100.0"), 100.0)
        self.assertEqual(converter("50.5"), 50.5)

        # Should fail for values above maximum
        with self.assertRaises(ValueError) as ctx:
            converter("101.0")
        self.assertIn("cannot be larger than", str(ctx.exception))


class IntTypeConverterTest(TestCase):
    def test_int_basic(self):
        """Test basic integer conversion"""
        converter = intType()
        self.assertEqual(converter("42"), 42)
        self.assertEqual(converter("-10"), -10)
        self.assertEqual(converter("0"), 0)

    def test_int_invalid(self):
        """Test integer conversion with invalid input"""
        converter = intType()

        with self.assertRaises(ValueError) as ctx:
            converter("not_an_int")
        self.assertIn("is not a valid integer", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            converter("3.14")
        self.assertIn("is not a valid integer", str(ctx.exception))

    def test_int_min_validation(self):
        """Test integer minimum validation"""
        converter = intType(min=0)

        # Should work for valid values
        self.assertEqual(converter("0"), 0)
        self.assertEqual(converter("10"), 10)

        # Should fail for values below minimum
        with self.assertRaises(ValueError) as ctx:
            converter("-1")
        self.assertIn("cannot be smaller than", str(ctx.exception))

    def test_int_max_validation(self):
        """Test integer maximum validation"""
        converter = intType(max=100)

        # Should work for valid values
        self.assertEqual(converter("100"), 100)
        self.assertEqual(converter("50"), 50)

        # Should fail for values above maximum
        with self.assertRaises(ValueError) as ctx:
            converter("101")
        self.assertIn("cannot be larger than", str(ctx.exception))


class FileTextConverterTest(TestCase):
    def test_file_read_mode(self):
        """Test opening file in read mode"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            tmp.write("test content")
            tmp_path = tmp.name

        try:
            converter = fileText(mode="r")
            result = converter(tmp_path)

            self.assertEqual(result.mode, "r")
            content = result.read()
            self.assertEqual(content, "test content")
            result.close()
        finally:
            Path(tmp_path).unlink()

    def test_file_write_mode(self):
        """Test opening file in write mode"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp:
            tmp_path = tmp.name

        try:
            converter = fileText(mode="w")
            result = converter(tmp_path)

            self.assertEqual(result.mode, "w")
            result.write("new content")
            result.close()

            # Verify content was written
            with open(tmp_path, 'r') as f:
                self.assertEqual(f.read(), "new content")
        finally:
            Path(tmp_path).unlink()

    def test_file_default_mode(self):
        """Test that default mode is read"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            tmp.write("default mode test")
            tmp_path = tmp.name

        try:
            converter = fileText()
            result = converter(tmp_path)

            self.assertEqual(result.mode, "r")
            result.close()
        finally:
            Path(tmp_path).unlink()

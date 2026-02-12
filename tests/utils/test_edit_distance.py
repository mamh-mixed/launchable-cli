from unittest import TestCase

from smart_tests.utils.edit_distance import edit_distance


class EditDistanceTest(TestCase):
    def test_edit_distance(self):
        def test(expected, a, b):
            self.assertEqual(expected, edit_distance(a, b))
            self.assertEqual(expected, edit_distance(b, a))

        test(0, "abc", "abc")
        test(2, "abc", "bac")
        test(1, "abc", "abcd")
        test(1, "abxc", "abc")

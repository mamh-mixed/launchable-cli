import inspect
from typing import Annotated, List
from unittest import TestCase

from smart_tests.args4p.parameter import to_type


class ParameterTest(TestCase):

    def test_to_type(self):
        # noinspection PyUnusedLocal
        def f(untyped, direct: int, compound: List[str],
              annotated: Annotated[int, 5],
              annotated_compound: Annotated[List[int], 5]):
            pass

        sig = inspect.signature(f)
        self.assertEqual(to_type(sig.parameters['untyped']), None)
        self.assertEqual(to_type(sig.parameters['direct']), int)
        self.assertEqual(to_type(sig.parameters['compound']), List[str])
        self.assertEqual(to_type(sig.parameters['annotated']), int)
        self.assertEqual(to_type(sig.parameters['annotated_compound']), List[int])

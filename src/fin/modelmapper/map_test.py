# (C) Steve Stagg

from __future__ import with_statement

import time
import cStringIO as StringIO
import unittest2 as unittest

import fin.modelmapper.map


class TestModel(fin.modelmapper.map.Mapped):

    def __init__(self, id=None, c=None):
        super(TestModel, self).__init__()
        self.id = id
        self.a = 1
        self.c = c

    a = fin.modelmapper.map.model("a")
    b = fin.modelmapper.map.model("b")
    c = fin.modelmapper.map.model("c")
    d = fin.modelmapper.map.model("d")
    e = fin.modelmapper.map.model("e")
    f = fin.modelmapper.map.model("f")

    def a_to_b(self):
        return "fromA"

    def a_to_c(self):
        time.sleep(2)
        return "fromA"

    def b_to_c(self):
        return "fromB"

    def other(self):
        return "other"

    MODEL_MAP = {
        ("a", "b"): a_to_b,
        ("a", "c"): a_to_c,
        ("b", "c"): b_to_c,
        ("c", "d"): other,
        ("d", "e"): other,
        ("b", "f"): other,
        ("e", "f"): other,
        ("e", "b"): other,
    }
    ORDERED_MAPPINGS = {
        'b': [('e',), ('a',), ('d', 'e'), ('c', 'd', 'e')],
        'c': [('b',), ('e', 'b'), ('a', 'b'), ('d', 'e', 'b')],
        'd': [('c',), ('b', 'c'), ('e', 'b', 'c'), ('a', 'b', 'c')],
        'e': [('d',), ('c', 'd'), ('b', 'c', 'd'), ('a', 'b', 'c', 'd')],
        'f': [('e',), ('b',), ('d', 'e'), ('a', 'b'), ('c', 'd', 'e')]
        }



def run_all_combinations():
    for i in range(10):
        tm = TestModel()
        tm.b
        tm.c
        tm.d
        tm.e
        tm.f
        tm.b = None
        tm.b


class ModelTest(unittest.TestCase):

    def test_simple(self):
        model = TestModel()
        self.assertEqual(model.a, 1)
        # The 'obvious' route is from a->c, which involves a 2s sleep
        # The better route is a->b->c
        self.assertEqual(model.c, "fromB")
        print model.b


if __name__ == "__main__":
    unittest.main()
from __future__ import with_statement

import random

import fin.testing as unittest

import fin.patch


class PatchTests(unittest.TestCase):

    def test_patching(self):
        class Foo(object):
            TRUE = True
        self.assertTrue(Foo.TRUE)
        with fin.patch.patch(Foo, "TRUE", False):
            self.assertFalse(Foo.TRUE)
        self.assertTrue(Foo.TRUE)

    def test_patching_library_func(self):
        nums = set()
        # Theoretically, this could fail, but the probability is very low
        for i in range(5):
            nums.add(random.random())
        self.assertTrue(len(nums) > 1)
        with fin.patch.patch(random, "random", lambda: 1):
            for i in range(5):
                self.assertTrue(random.random(), 1)
        nums = set()
        for i in range(5):
            nums.add(random.random())
        self.assertTrue(len(nums) > 1)

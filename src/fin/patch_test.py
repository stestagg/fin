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
        a = random.random()
        b = random.random()        
        self.assertNotEqual(a, b)
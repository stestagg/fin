
from __future__ import with_statement

import os
import shutil
import tempfile

import fin.testing
import fin.duplex


class DuplexTest(fin.testing.TestCase):

    def test_duplex_definition(self):
        class A(object):
            def abc(self):
                return self

            @fin.duplex.method
            def xyz(self):
                return self

        a = A()
        self.assertIs(A.xyz(), A)
        self.assertIs(a.xyz(), a)

    def test_duplex_definition_call(self):
        class A(object):
            def abc(self):
                return self

            @fin.duplex.method()
            def xyz(self):
                return self

        a = A()
        self.assertIs(A.xyz(), A)
        self.assertIs(a.xyz(), a)

    def test_custom_lookup_func(self):
        def find_a(cls):
            return cls.INST

        class A(object):
            INST = None
            @fin.duplex.method(inst_lookup_fun=find_a)
            def me(self):
                return self

        a = A()
        A.INST = a
        self.assertIs(A.me(), a)
        self.assertIs(a.me(), a)

        class B(A):
            pass
        b = B()
        self.assertIs(B.me(), a)
        self.assertIs(b.me(), b)

        B.INST = b
        self.assertIs(A.me(), a)
        self.assertIs(a.me(), a)
        self.assertIs(B.me(), b)
        self.assertIs(b.me(), b)
        A.INST = None
        B.INST = None

    def test_different_classmethod(self):
        INST = object()
        CLS = object()
        class A(object):
            @fin.duplex.method
            def thefunc(self):
                return INST, self

            @thefunc.classmethod
            def thefunc(cls):
                return CLS, cls

        a = A()
        self.assertEqual(A.thefunc(), (CLS, A))
        self.assertEqual(a.thefunc(), (INST, a))


if __name__ == "__main__":
    fin.testing.main()

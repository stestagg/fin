import tempfile
import shutil
import os

import fin.testing as unittest
import fin.abstract

import fin.module_test


class AbstractTest(unittest.TestCase):

    def test_simple_subclass(self):
        class B(fin.abstract.Class):
            pass
        self.assertCountEqual([B], B.all_types())
        class C(B):
            pass
        self.assertCountEqual([B, C], B.all_types())
        self.assertCountEqual([], B.all_types_with_name())
        class D(B):
            NAME = "d"
        self.assertCountEqual([D], B.all_types_with_name())
        self.assertCountEqual([B, C, D], D.all_types())
        class E(D):
            NAME = "e"
        self.assertCountEqual([B, C, D, E], E.all_types())
        self.assertCountEqual([D, E], B.all_types_with_name())
        class F(C):
            NAME = "f"
        self.assertCountEqual([B, C, D, E, F], F.all_types())
        self.assertCountEqual([D, E, F], B.all_types_with_name())
        self.assertEqual(B.type_by_name("f"), F)
        self.assertEqual(B.type_by_name("d"), D)

    def test_name_errors(self):
        class B(fin.abstract.Class):
            pass
        class C(B):
            NAME = "same"
        class D(B):
            NAME = "same"
        self.assertCountEqual([B, C, D], B.all_types())
        self.assertCountEqual([C, D], B.all_types_with_name())
        with self.assertRaises(KeyError):
            B.type_by_name("foo")
        with self.assertRaisesRegex(Exception, "Multiple subclasses found with NAME: same"):
            B.type_by_name("same")


class AbstractImportTest(unittest.TestCase):

    def setUp(self):
        self.temp_dir = None

    def tearDown(self):
        if self.temp_dir is not None:
            shutil.rmtree(self.temp_dir)

    @property
    def fixture_modules(self):
        if self.temp_dir is None:
            self.temp_dir = tempfile.mkdtemp()
            fin.module_test.make_tree(self.temp_dir, {
                "a": {"foos": {}},
                })
            for init_path in [(), ("a", ), ("a", "foos")]:
                file_parts = init_path + ("__init__.py", )
                open(os.path.join(self.temp_dir, *file_parts), "wb").close()
            with open(os.path.join(self.temp_dir, "a", "foo.py"), "wb") as fh:
                fh.write(b"import fin.abstract\nclass Foo(fin.abstract.Class):\n  pass")
            for py, name in [
                (("a", "foos", "sa.py"), "A"),
                (("a", "foos", "sb.py"), "B"),
                (("a", "foos", "sc.py"), "C"),
                (("a", "foos", "sd.py"), "D"),
                ]:
                with open(os.path.join(self.temp_dir, *py), "wb") as fh:
                    fh.write(("import a.foo\nclass %s(a.foo.Foo):\n  NAME='%s'" % (name, name, )).encode('utf-8'))
        return self.temp_dir

    def test_subs(self):
        fixture_modules = self.fixture_modules
        with fin.module_test.module_context(fixture_modules):
            import a.foo
            self.assertCountEqual(a.foo.Foo.all_types(), (a.foo.Foo, ))
            self.assertCountEqual(a.foo.Foo.all_types_with_name(), ())
            a.foo.Foo.load_subclasses()
            self.assertCountEqual([t.__name__ for t in a.foo.Foo.all_types()], 
                                  ("Foo", "A", "B", "C", "D"))
            with open(os.path.join(self.temp_dir, "a", "foos", "serr.py"), "wb") as fh:
                fh.write(b"die")
            with self.assertRaises((NameError, ImportError)):
                a.foo.Foo.load_subclasses()


if __name__ == "__main__":
    unittest.main()


from __future__ import with_statement

import inspect
import sys
import os
import contextlib
import tempfile
import shutil

import fin.testing as unittest
import fin.color
import fin.module


@contextlib.contextmanager
def module_context(path):
    sys_module_keys = frozenset(sys.modules.keys())
    old_syspath = sys.path[:]
    sys.path.insert(0, path)
    try:
        yield
    finally:
        sys.path = old_syspath
        for key in sys.modules.keys():
            if key not in sys_module_keys:
                del sys.modules[key]


def make_tree(base, sub):
    if isinstance(sub, basestring):
        os.mkdir(os.path.join(base, sub))
    elif isinstance(sub, (list, tuple)):
        for sub_dir in sub:
            make_tree(base, sub_dir)
    else:
        for sub, children in sub.iteritems():
            make_tree(base, sub)
            make_tree(os.path.join(base, sub), children)


class ModuleTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = None

    def tearDown(self):
        if self.temp_dir is not None:
            shutil.rmtree(self.temp_dir)

    @property
    def test_modules(self):
        if self.temp_dir is None:
            self.temp_dir = tempfile.mkdtemp()
            make_tree(self.temp_dir, {
                "a": {"b": {"c": "d"}},
                "a2": {"b": "c", "b.2": "c2"},
                "n": {"n": {"a": "b"}}
                })
            for init_path in [
                ("a", ), ("a", "b"), ("a", "b", "c"),
                ("a2", ), ("a2", "b"), ("a2", "b.2"), ("a2", "b.2", "c2"),
                ("n", "n", "a"), ("n", "n", "a", "b")
                ]:
                file_parts = init_path + ("__init__.py", )
                open(os.path.join(self.temp_dir, *file_parts), "wb").close()
            for py in [
                ("a", "b", "ab.py"),
                ("a", "b", "ab2.py"),
                ("a2", "b.2", "a2b2.py"),
                ("a2", "b.2", "c2", "a2b2c.py"),
                ("n", "n", "a", "nna.py"),
                ("n", "n", "a", "_private.py"),
                ]:
                with open(os.path.join(self.temp_dir, *py), "wb") as fh:
                    fh.write("import string\nME=%r\n" % (py[-1], ))
        return self.temp_dir

    def test_get_fully_qualified_object(self):
        with self.assertRaises(NameError):
            urllib2.AbstractHttpHandler.do_open
        do_open = fin.module.get_fully_qualified_object(
            "urllib2.AbstractHTTPHandler.do_open")
        self.assertEqual(do_open.__name__, "do_open")

    def test_longer_path(self):
        # Slightly fragile, but more complex example
        ltrim = fin.module.get_fully_qualified_object(
            "fin.color.fin.string.ltrim")
        self.assertEqual(ltrim("abacus", "ab"), "acus")

    def test_already_imported(self):
        red = fin.module.get_fully_qualified_object("fin.color.C.red")
        self.assertEqual(red("blue"), fin.color.C.red("blue"))

    def test_bad_objects(self):
        with self.assertRaisesRegexp(AttributeError,
                                     "'sys' does not contain 'fail'"):
            fin.module.get_fully_qualified_object("sys.fail")
        with self.assertRaisesRegexp(
            AttributeError, "'fin.module.get_fully_qualified_object'"
                            " does not contain 'fail'"):
            fin.module.get_fully_qualified_object(
                "fin.module.get_fully_qualified_object.fail")

    def test_finding_module(self):
        base = self.test_modules
        with module_context(self.test_modules):
            def test(parts, equals="", auto_add=False):
                module_parts = parts.split("/")
                equals = equals.split(".")
                result = fin.module.path_to_module_parts(
                    os.path.join(base, *module_parts), auto_add=auto_add)
                self.assertSequenceEqual(result, equals)
            test("a/b", "a.b")
            test("a2/b", "a2.b")
            with self.assertRaises(fin.module.PathNotImportable):
                test("a2/b.2")
            with self.assertRaises(fin.module.NoSysPathFound):
                test("a2/b.2/a2b2.py")
        with module_context(self.test_modules):
            test("a2/b.2/a2b2.py", "a2b2", True)
            assert os.path.join(self.test_modules, "a2", "b.2") in sys.path
        assert os.path.join(self.test_modules, "a2", "b.2") not in sys.path
        with module_context(self.test_modules):
            test("a2/b.2/c2/a2b2c.py", "c2.a2b2c", True)
            assert os.path.join(self.test_modules, "a2", "b.2") in sys.path
        with module_context(self.test_modules):
            with self.assertRaises(fin.module.NoSysPathFound):
                test("n/n/a")
            test("n/n/a/nna.py", "a.nna", True)

    def test_importing(self):
        with module_context(self.test_modules):
            ab = fin.module.import_module_by_name_parts("a", "b", "ab")
            self.assertEqual(ab.ME, "ab.py")
            with self.assertRaises(ImportError):
                fin.module.import_module_by_name_parts("n", "n", "a", "nna")

    def test_importing_child_modules(self):
        with module_context(self.test_modules):
            mods = fin.module.import_child_modules(["a", "b"])
            self.assertEqual(mods["ab"].ME, "ab.py")
            self.assertEqual(mods["ab2"].ME, "ab2.py")
            with open(os.path.join(self.test_modules, "a", "b", "err.py"), "wb") as fh:
                fh.write("import thisdoesntexist\n")
            with self.assertRaises(ImportError):
                fin.module.import_child_modules(["a", "b"])
            new_mods = fin.module.import_child_modules(["a", "b"], error_callback=lambda *x: None)
            self.assertEqual(mods, new_mods)
            import_errors = []

            def on_error(e):
                import_errors.append(e)

            fin.module.import_child_modules(["a", "b"], error_callback=on_error)
            # This should be exactly 1, but py/pycs
            self.assertTrue(len(import_errors) > 1)
            for error in import_errors:
                self.assertIsInstance(error, ImportError)

    def test_child_modules_as_dirs(self):
        with module_context(self.test_modules):
            os.mkdir(os.path.join(self.test_modules, "x"))
            open(os.path.join(self.temp_dir, "x", "__init__.py"), "wb").close()
            with open(os.path.join(self.temp_dir, "x", "AA.py"), "wb") as fh:
                fh.write("FOO='AA'")
            with open(os.path.join(self.temp_dir, "x", "BB.py"), "wb") as fh:
                fh.write("FOO='BB'")
            os.mkdir(os.path.join(self.test_modules, "x", "y"))
            with open(os.path.join(self.temp_dir, "x", "y", "__init__.py"), "wb") as fh:
                fh.write("FOO='y'")
            modules = fin.module.import_child_modules(["x"])
            for name in ["AA", "BB", "y"]:
                self.assertEqual(modules[name].FOO, name)

    def test_importing_by_path(self):
        def get(rel_path, auto_add=False):
            with module_context(self.test_modules):
                return fin.module.import_module_by_path(
                    os.path.join(self.test_modules, *rel_path.split("/")),
                    auto_add=auto_add)

        ab = get("a/b/ab.py")
        self.assertEqual(ab.ME, "ab.py")
        with self.assertRaises(ImportError):
            get("n/n/a/nna.py")
        with self.assertRaises(ImportError):
            get("n/n/a/nothing.py")
        self.assertEqual(get("n/n/a/nna.py", auto_add=True).ME, "nna.py")

    def test_qualified_object(self):
        with module_context(self.test_modules):
            self.assertEqual(fin.module.get_fully_qualified_object("a.b.ab.ME"), "ab.py")
            lowercase = fin.module.get_fully_qualified_object(
                "a.b.ab.string.lowercase")
            self.assertEqual(lowercase[0], "a")

    def test_importing_library_module(self):
        with module_context(self.test_modules):
            sys_email = fin.module.import_module_by_name_parts("email")
        with module_context(self.test_modules):
            self.assertSequenceEqual(
                fin.module.path_to_module_parts(inspect.getfile(sys_email)), ["email"])
        with module_context(self.test_modules):
            math_mod = fin.module.import_module_by_name_parts("math")
            self.assertAlmostEqual(math_mod.pi, 3.141, places=2)


if __name__ == "__main__":
    unittest.main()



from __future__ import with_statement

import os
import shutil
import tempfile

import fin.testing
import fin.config


class EnvironSourceTest(fin.testing.TestCase):

    def setUp(self):
        self.before = os.environ.copy()
        os.environ.clear()

    def tearDown(self):
        os.environ.clear()
        for key, value in self.before.iteritems():
            os.environ[key] = value

    def test_getting_simple(self):
        os.environ["FOO_BAR"] = "a"
        os.environ["FOOBAR"] = "b"
        source = fin.config.EnvironSource("FOO", sep="_")
        self.assertEqual(source.get_value("BaR"), "a")
        self.assertEqual(source.get_value("notthere"), fin.config.NOT_SET)

    def test_getting_nested(self):
        os.environ["FOO.BAR"] = "a"
        os.environ["FOO.BAR.BAZ"] = "b"
        source = fin.config.EnvironSource("FOO")
        self.assertEqual(source.get_value("BAR"), "a")
        self.assertEqual(source.get_value("BAR", "baz"), "b")

    def test_getting_children(self):
        os.environ["FOO_BAR"] = "a"
        os.environ["FOO_BAR_BAZ"] = "b"
        os.environ["FOO_BAR_BOB"] = "c"
        source = fin.config.EnvironSource("FOO", sep="_")
        self.assertItemsEqual(source.get_keys(), ["bar"])
        self.assertItemsEqual(source.get_keys("BaR"), ["baz", "bob"])


class ConfigParserTest(fin.testing.TestCase):

    def setUp(self):
        fd, self.config_path = tempfile.mkstemp()
        self.file = os.fdopen(fd, "wb", 0)
        self.file.write(
            "\n".join(["[.]",
            "first.a=1", "zero.c=2", "second.a.b=9",
            "first.c.sub2=8",
            "[FiRsT]", "a=3", "b=4", "c.sub=5",
            "[first]", "b = 6", "d=7", "[second]", "b=4",
            "[third]", "a.b=12"]))
        self.source = fin.config.ConfigParserSource(self.config_path)

    def tearDown(self):
        self.file.close()
        os.unlink(self.config_path)

    def test_get_keys(self):
        self.assertItemsEqual(self.source.get_keys(),
                              ["zero", "first", "second", "third"])
        self.assertItemsEqual(self.source.get_keys("first"),
                              ["a", "b", "c", "d"])
        self.assertItemsEqual(self.source.get_keys("first", "c"),
                              ["sub", "sub2"])
        self.assertItemsEqual(self.source.get_keys("second"), ["a", "b"])
        self.assertItemsEqual(self.source.get_keys("third"), ["a"])
        self.assertItemsEqual(self.source.get_keys("fourth"), [])

    def test_get_value(self):
        self.assertEqual(self.source.get_value("first", "a"), "1")
        self.assertEqual(self.source.get_value("first", "c", "sub"), "5")
        self.assertEqual(self.source.get_value("first", "b"), "6")
        self.assertEqual(self.source.get_value("first", "notthere"), fin.config.NOT_SET)
        self.assertEqual(self.source.get_value("third", "a", "b"), "12")


class DictConfigTest(fin.testing.TestCase):

    def test_get_value(self):
        source = fin.config.DictSource({"a": 1})
        self.assertEqual(source.get_value("a"), "1")
        self.assertEqual(source.get_value("b"), fin.config.NOT_SET)

    def test_get_nested_value(self):
        source = fin.config.DictSource({"a": {"b": 2}})
        self.assertEqual(source.get_value("a", "b"), "2")
        self.assertEqual(source.get_value("a", "c"), fin.config.NOT_SET)

    def test_get_keys(self):
        source = fin.config.DictSource({"a": {"b": 2, "c": {"d": 3}}})
        self.assertItemsEqual(source.get_keys("a"), ["b", "c"])
        self.assertItemsEqual(source.get_keys("b"), [])
        self.assertItemsEqual(source.get_keys("a", "b"), [])
        self.assertItemsEqual(source.get_keys("a", "c"), ["d"])


class MultiSourceTest(fin.testing.TestCase):

    def test_get_value(self):
        sources = [fin.config.DictSource(f) for f in [{"a": 1}, {"b": 2}]]
        source = fin.config.MultiSource(sources)
        self.assertEqual(source.get_value("a"), "1")
        self.assertEqual(source.get_value("b"), "2")
        self.assertEqual(source.get_value("c"), fin.config.NOT_SET)

    def test_override(self):
        sources = [fin.config.DictSource(f) for f in [{"a": 1, "b": 2}, {"b": 3, "c":4}]]
        source = fin.config.MultiSource(sources)
        self.assertEqual(source.get_value("a"), "1")
        self.assertEqual(source.get_value("b"), "3")
        self.assertEqual(source.get_value("c"), "4")

    def test_get_nested(self):
        sources = [fin.config.DictSource(f) for f in [
            {"a": {"b": 1, "c": 2}},
            {"a": {"b": 4, "d": 5}, "b": 3}]]
        source = fin.config.MultiSource(sources)
        self.assertItemsEqual(source.get_keys(), ["a", "b"])
        self.assertItemsEqual(source.get_keys("a"), ["b", "c", "d"])
        self.assertItemsEqual(source.get_keys("a", "b"), [])
        self.assertItemsEqual(source.get_keys("f"), [])


class JsonTest(fin.testing.TestCase):

    def setUp(self):
        self.raw = """{"A": 1, "b": {"a": 2}}"""
        self.config = fin.config.JSONSource("", data=self.raw)
        try:
            self.config.json
        except RuntimeError:
            raise fin.testing.unittest.SkipTest("No JSON library available")

    def test_keys(self):
        self.assertItemsEqual(self.config.get_keys(), ["a", "b"])
        self.assertItemsEqual(self.config.get_keys("b"), ["a"])

    def test_get_value(self):
        self.assertEqual(self.config["b", "a"], '2')


class ConfigTest(fin.testing.TestCase):

    def setUp(self):
        self.before = os.environ.copy()
        os.environ.clear()
        self.source = fin.config.Config("fintests")

    def tearDown(self):
        os.environ.clear()
        for key, value in self.before.iteritems():
            os.environ[key] = value

    def test_simple(self):
        os.environ["FINTESTS_FOO"] = "1"
        self.assertEqual(self.source.get_value("FOO"), "1")
        self.assertEqual(self.source.get_value("BAR"), fin.config.NOT_SET)

    def test_with_file(self):
        os.environ["FINTESTS_FOO"] = "1"
        tempdir = tempfile.mkdtemp()
        try:
            os.environ["XDG_CONFIG_HOME"] = tempdir
            with open(os.path.join(tempdir, "fintests.conf"), "wb") as fh:
                fh.write("[.]\nFOO=2\nBAR=3")
            self.assertEqual(self.source.get_value("FOO"), "1")
            self.assertEqual(self.source.get_value("BAR"), "3")
        finally:
            shutil.rmtree(tempdir)

    def test_getitem(self):
        os.environ["FINTESTS_FOO"] = "1"
        os.environ["FINTESTS_BAR_BAZ"] = "2"
        self.assertEqual(self.source["fOo"], "1")
        with self.assertRaises(KeyError):
            self.source["bar"]
        self.assertIsNone(self.source.get("bAr"))
        self.assertEqual(self.source.get("bAr", "test"), "test")
        self.assertEqual(self.source.get("baR.Baz", "test"), "2")
        self.assertEqual(self.source.get(("BAR", "BAZ"), "test"), "2")
        self.assertEqual(self.source["bar", "BAZ"], "2")
        self.assertEqual(self.source["bar.BAZ"], "2")


class TypedTest(fin.testing.TestCase):

    class TypedConf(fin.config.DictSource, fin.config.TypedConfig):
        pass

    def test_get_bool(self):
        conf = self.TypedConf({"a": "yes", "b": "no"})
        self.assertEqual(conf.get_typed(bool, "a"), True)
        self.assertEqual(conf.get_typed(bool, "b"), False)

    def test_get_int(self):
        conf = self.TypedConf({"a": "1", "b": "2", "c": "foo"})
        self.assertEqual(conf.get_typed(int, "a"), 1)
        self.assertEqual(conf.get_typed(int, "b"), 2)
        self.assertEqual(conf.get_typed(int, "d"), None)
        self.assertEqual(conf.get_typed(int, "d", "foo"), "foo")
        with self.assertRaises(ValueError):
            conf.get_typed(int, "c")


if __name__ == "__main__":
    fin.testing.main()

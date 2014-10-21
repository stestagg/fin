# (C) Steve Stagg

from __future__ import with_statement

import fin.testing as unittest
import fin.contextlog


class ContextLogTests(unittest.TestCase):

    def setUp(self):
        self.data = []

    def write(self, msg):
        self.data.append(msg)

    def isatty(self):
        return False

    def flush(self):
        pass

    @property
    def lines(self):
        return ("".join(self.data)).splitlines()

    def test_simple_log(self):
        with fin.contextlog.Log("Foo", stream=self):
            with fin.contextlog.Log("Bar", stream=self):
                pass
        self.assertEqual(self.lines, ["Foo: ", "| Bar: OK", "`- OK"])

    def test_traceback(self):
        with self.assertRaises(ZeroDivisionError):
            with fin.contextlog.Log("Foo", stream=self):
                1/0
        self.assertEqual(self.lines, ["Foo: FAIL"])

    def test_nested_traceback(self):
        with self.assertRaises(ZeroDivisionError):
            with fin.contextlog.Log("Foo", stream=self):
                with fin.contextlog.Log("Bar", stream=self):
                    1/0
                    self.assertEqual(self.lines,
                         ["Foo: ", "|  Bar: FAIL", "`- FAIL"])

    def test_output(self):
        with fin.contextlog.Log("A", stream=self) as log:
            log.output("b")
            log.output("c")
            with fin.contextlog.Log("B", stream=self) as l2:
                l2.output("d\ne")
                with fin.contextlog.Log("C", stream=self):
                    pass
        self.assertEqual("\n".join(l.strip() for l in self.lines), """A:
| + b
| + c
| B:
| | + d
| | + e
| | C: OK
| `- OK
`- OK""")

    def test_clog(self):
        with fin.contextlog.CLog("Foo", stream=self):
            with fin.contextlog.CLog("Bar", stream=self):
                pass
        self.assertEqual(self.lines, [])

    def test_clog_with_log(self):
        with fin.contextlog.CLog("Foo", stream=self):
            with fin.contextlog.CLog("Bar", stream=self):
                with fin.contextlog.Log("Baz", stream=self):
                    pass
        self.assertEqual(self.lines,
                         ["Foo: ", "| Bar: ", "| | Baz: OK", "| `- OK", "`- OK"])

    def test_clog_with_log2(self):
        with fin.contextlog.CLog("1", stream=self):
            with fin.contextlog.CLog("2", stream=self):
                pass
            with fin.contextlog.CLog("3", stream=self):
                with fin.contextlog.Log("4", stream=self):
                    pass
        self.assertEqual(self.lines,
                         ["1: ", "| 3: ", "| | 4: OK", "| `- OK", "`- OK"])

    def test_clog_exception(self):
        with self.assertRaises(ZeroDivisionError):
            with fin.contextlog.CLog("Foo", stream=self):
                with fin.contextlog.CLog("Bar", stream=self):
                    1/0
        self.assertEqual(self.lines, ["Foo: ", "| Bar: ",
                                      "| `- FAIL", "`- FAIL"])

    def test_incorrect_log_output(self):
        with self.assertRaises(ValueError):
            with fin.contextlog.Log("Foo", stream=self) as l:
                l.output("Works")
            l.output("Fails")
        self.assertEqual(self.lines, ["Foo: ", "| + Works", "`- OK"])

    def test_log_output_format(self):
        with fin.contextlog.Log("Foo", stream=self) as l:
            l.format({1: "2"})
        self.assertEqual(self.lines, ["Foo: ", "| + {1: '2'}", "`- OK"])


if __name__ == "__main__":
    unittest.main()


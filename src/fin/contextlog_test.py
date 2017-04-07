# (C) Steve Stagg

import io
import functools

import fin.testing as unittest
import fin.contextlog


class ContextLogTests(unittest.TestCase):

    def setUp(self):
        self.data = []

    def write(self, msg):
        if hasattr(msg, "decode"):
            msg = msg.decode("utf-8")
        self.data.append(msg)

    def isatty(self):
        return False

    def flush(self):
        pass

    @property
    def lines(self):
        return ("".join(self.data)).splitlines()

    def test_simple_log(self):
        with fin.contextlog.Log("Foo", stream=self, theme='plain'):
            with fin.contextlog.Log("Bar", stream=self, theme='plain'):
                pass
        self.assertEqual(self.lines, ["Foo: ", "| Bar: OK", "`- OK"])

    def test_traceback(self):
        with self.assertRaises(ZeroDivisionError):
            with fin.contextlog.Log("Foo", stream=self, theme='plain'):
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
        with fin.contextlog.Log("A", stream=self, theme='plain') as log:
            log.output("b")
            log.output("c")
            with fin.contextlog.Log("B", stream=self, theme='plain') as l2:
                l2.output("d\ne")
                with fin.contextlog.Log("C", stream=self, theme='plain'):
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
        with fin.contextlog.CLog("Foo", stream=self, theme='plain'):
            with fin.contextlog.CLog("Bar", stream=self, theme='plain'):
                with fin.contextlog.Log("Baz", stream=self, theme='plain'):
                    pass
        self.assertEqual(self.lines,
                         ["Foo: ", "| Bar: ", "| | Baz: OK", "| `- OK", "`- OK"])

    def test_clog_with_log2(self):
        with fin.contextlog.CLog("1", stream=self, theme='plain'):
            with fin.contextlog.CLog("2", stream=self, theme='plain'):
                pass
            with fin.contextlog.CLog("3", stream=self, theme='plain'):
                with fin.contextlog.Log("4", stream=self, theme='plain'):
                    pass
        self.assertEqual(self.lines,
                         ["1: ", "| 3: ", "| | 4: OK", "| `- OK", "`- OK"])

    def test_clog_exception(self):
        with self.assertRaises(ZeroDivisionError):
            with fin.contextlog.CLog("Foo", stream=self, theme='plain'):
                with fin.contextlog.CLog("Bar", stream=self, theme='plain'):
                    1/0
        self.assertEqual(self.lines, ["Foo: ", "| Bar: ",
                                      "| `- FAIL", "`- FAIL"])

    def test_incorrect_log_output(self):
        with self.assertRaises(ValueError):
            with fin.contextlog.Log("Foo", stream=self, theme='plain') as l:
                l.output("Works")
            l.output("Fails")
        self.assertEqual(self.lines, ["Foo: ", "| + Works", "`- OK"])

    def test_log_output_format(self):
        with fin.contextlog.Log("Foo", stream=self, theme='plain') as l:
            l.format({1: "2"})
        self.assertEqual(self.lines, ["Foo: ", "| + {1: '2'}", "`- OK"])

    def test_anonymous_output(self):
        with fin.contextlog.Log("Foo", stream=self, theme='plain'):
            fin.contextlog.Log.output("Test")
        self.assertEqual(self.lines, ['Foo: ', '| + Test', '`- OK'])

    def test_anonymous_nested_output(self):
        with fin.contextlog.Log("Foo", stream=self, theme='plain'):
            with fin.contextlog.Log("Bar", stream=self, theme='plain'):
                fin.contextlog.Log.output("Test")
        self.assertEqual(self.lines, ['Foo: ', '| Bar: ', '| | + Test', '| `- OK', '`- OK'])

    def test_anonymous_output_noleak(self):
        with fin.contextlog.Log("Foo", stream=self, theme='plain'):
            with fin.contextlog.Log("Bar", stream=self, theme='plain'):
                fin.contextlog.Log.output("ONE")
            fin.contextlog.Log.output("TWO")
        self.assertEqual(self.lines, ['Foo: ', '| Bar: ', '| | + ONE', '| `- OK', '| + TWO', '`- OK'])

    def test_outputting_to_text_buffer(self):
        stream = io.StringIO()
        bytes_as_str = str(b'hi')
        with fin.contextlog.Log("Foo", stream=stream, theme='plain') as l:
            l.format(b'hi')
            l.output('ho')
        self.assertEqual(stream.getvalue(), "Foo: \n| + %s\n| + ho\n`- OK\n" % bytes_as_str)

    def test_outputting_to_bytes_buffer(self):
        stream = io.BytesIO()
        bytes_as_str = str(b'hi')
        with fin.contextlog.Log("Foo", stream=stream, theme='plain') as l:
            l.format(b'hi')
            l.output('ho')
        self.assertEqual(stream.getvalue().decode('utf-8'), u"Foo: \n| + %s\n| + ho\n`- OK\n" % bytes_as_str)

    def test_outputting_as_string_and_bytes(self):
        for stream_type in [io.StringIO, io.BytesIO]:
            stream = stream_type()
            Log = functools.partial(fin.contextlog.Log, stream=stream, theme='plain')
            with Log("One"):
                with Log("Two") as l:
                    l.output('Three')
                    l.format({'a': b'a', 1: 2.1})
                try:
                    with Log("Fail"):
                        raise IndexError()
                except IndexError:
                    pass

    def test_not_closing_context(self):
        stream = io.BytesIO()
        with fin.contextlog.Log("Foo", stream=stream, theme='plain'):
            fin.contextlog.Log("Bar", stream=stream, theme='plain').__enter__()
        with fin.contextlog.Log("Baz", stream=stream, theme='plain'):
            pass
        self.assertEqual(stream.getvalue(), b'Foo: \n| Bar: OK\n`- OK\nBaz: OK\n')

if __name__ == "__main__":
    unittest.main()


# (C) Steve Stagg

import fin.testing as unittest

import fin.string


class StringTests(unittest.TestCase):
    
    def test_ltrim(self):
        for inp, prefix, expected in [
            ("test", ("tes",), "t"),
            ("b", ("b",), ""),
            ("test", ("bob", "cat"), "test"),
            ("test", ("tess", "tea"), "test"),
            ("test", ("te", "tes"), "st"),
            ("test", ("test",), ""),
            ]:
            self.assertEqual(fin.string.ltrim(inp, *prefix), expected)
            self.assertEqual(fin.string.String("Foo").ltrim("F"), "oo")
            self.assertEqual(fin.string.String(u"Foo").ltrim("F"), "oo")

    def test_rtrim(self):
        for inp, prefix, expected in [
            ("test", ("est",), "t"),
            ("b", ("b",), ""),
            ("test", ("bob", "cat"), "test"),
            ("test", ("tt", "ast"), "test"),
            ("test", ("st", "test"), "te"),
            ("test", ("test",), ""),
            ]:
            self.assertEqual(fin.string.rtrim(inp, *prefix), expected)
            self.assertEqual(fin.string.String("Foo").rtrim("oo"), "F")
            self.assertEqual(fin.string.String(u"Foo").rtrim("oo"), "F")


if __name__ == "__main__":
    unittest.main()


# (C) Steve Stagg

import unittest2 as unittest

import fin.color
import fin.util


class UtilTests(unittest.TestCase):

    def test_get_fully_qualified_object(self):
        with self.assertRaises(NameError):
            urllib2.AbstractHttpHandler.do_open
        do_open = fin.util.get_fully_qualified_object(
            "urllib2.AbstractHTTPHandler.do_open")
        self.assertEqual(do_open.__name__, "do_open")

    def test_longer_path(self):
        # Slightly fragile, but more complex example
        red = fin.util.get_fully_qualified_object(
            "fin.subtest.results.verbose.C.red")
        self.assertEqual(red("blue"), fin.color.C.red("blue"))

    def test_already_imported(self):
        red = fin.util.get_fully_qualified_object("fin.color.C.red")
        self.assertEqual(red("blue"), fin.color.C.red("blue"))

    def test_bad_objects(self):
        with self.assertRaisesRegexp(AttributeError,
                                     "'sys' does not contain 'fail'"):
            fin.util.get_fully_qualified_object("sys.fail")
        with self.assertRaisesRegexp(
            AttributeError, "'fin.util.get_fully_qualified_object'"
                            " does not contain 'fail'"):
            fin.util.get_fully_qualified_object(
                "fin.util.get_fully_qualified_object.fail")



if __name__ == "__main__":
    unittest.main()


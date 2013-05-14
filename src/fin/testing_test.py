import contextlib
import unittest

import fin.testing


def test_cm():
    results = []

    @contextlib.contextmanager
    def the_cm():
        results.append("before")
        try:
            yield
        except Exception, e:
            results.append(e)
        else:
            results.append("after")
    return results, the_cm


class TestingTest(unittest.TestCase):

    def test_enter(self):
        results, the_cm = test_cm()

        class TestTest(fin.testing.TestCase):
            def setUp(self):
                self._enter(the_cm())

            def runTest(self):
                self.assertTrue(True)

        test_inst = TestTest()
        test_inst.run()
        self.assertEqual(results, ["before", "after"])


if __name__ == "__main__":
    unittest.main()
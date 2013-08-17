
import fin.testing as unittest

import fin.color


class ColorTests(unittest.TestCase):

    def test_vtcolor(self):
        c = fin.color.VtColor()
        self.assertEqual(str(c.red), "\x1b[31m")
        self.assertEqual(str(c.red.bold), "\x1b[31;1m")
        self.assertEqual(str(c.red.bold.bg_yellow), "\x1b[31;1;43m")
        self.assertEqual(str(c.red + c.bold + c.reset), "\x1b[31;1;0m")
        self.assertEqual(str(c.red("test")), "\x1b[31mtest\x1b[0m")

    def test_nocolor(self):
        c = fin.color.NoColor()
        self.assertEqual(str(c.red), "")
        self.assertEqual(str(c.red.bold), "")
        self.assertEqual(str(c.red + c.bold + c.reset), "")
        self.assertEqual(str(c.red("test")), "test")


if __name__ == "__main__":
    unittest.main()


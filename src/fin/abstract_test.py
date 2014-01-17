import fin.testing as unittest
import fin.abstract


class AbstractTest(unittest.TestCase):

    def test_simple_subclass(self):
        class B(fin.abstract.Class):
            pass
        self.assertItemsEqual([B], B.all_types())
        class C(B):
            pass
        self.assertItemsEqual([B, C], B.all_types())
        self.assertItemsEqual([], B.all_types_with_name())
        class D(B):
            NAME = "d"
        self.assertItemsEqual([D], B.all_types_with_name())
        self.assertItemsEqual([B, C, D], D.all_types())
        class E(D):
            NAME = "e"
        self.assertItemsEqual([B, C, D, E], E.all_types())
        self.assertItemsEqual([D, E], B.all_types_with_name())
        class F(C):
            NAME = "f"
        self.assertItemsEqual([B, C, D, E, F], F.all_types())
        self.assertItemsEqual([D, E, F], B.all_types_with_name())
        self.assertEqual(B.type_by_name("f"), F)
        self.assertEqual(B.type_by_name("d"), D)

    def test_name_errors(self):
        class B(fin.abstract.Class):
            pass
        class C(B):
            NAME = "same"
        class D(B):
            NAME = "same"
        self.assertItemsEqual([B, C, D], B.all_types())
        self.assertItemsEqual([C, D], B.all_types_with_name())
        with self.assertRaises(KeyError):
            B.type_by_name("foo")
        with self.assertRaisesRegexp(Exception, "Multiple subclasses found with NAME: same"):
            B.type_by_name("same")

        

if __name__ == "__main__":
    unittest.main()


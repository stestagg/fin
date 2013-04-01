
try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestCase(unittest.TestCase):
    pass


def main(*args, **kwargs):
    unittest.main(*args, **kwargs)
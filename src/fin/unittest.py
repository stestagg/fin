
try:
	import unittest2 as unittest
except ImportError:
	import unittest

print unittest
print unittest.__file__

class TestCase(unittest.TestCase):
	pass


def main(*args, **kwargs):
	unittest.main(*args, **kwargs)
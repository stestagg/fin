import sys

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import fin.exception


NO_ITEMS = []


class TeardownErrors(fin.exception.Exception):
    pass


class TestCase(unittest.TestCase):

    def _enter(self, context_manager):
        if not hasattr(self, "_fin_context_managers"):
            self._fin_context_managers = []
        result = context_manager.__enter__()
        self._fin_context_managers.append(context_manager)
        return result

    def _exit(self, exc=None):
        if exc is None:
            exc_type = None
            tb = None
        else:
            _, _, tb = sys.exc_info()
            exc_type = type(exc)

        teardown_errors = []
        managers = getattr(self, "_fin_context_managers", NO_ITEMS)
        while managers:
            manager = managers.pop()
            try:
                manager.__exit__(exc_type, exc, tb)
            except Exception, e:
                teardown_errors.append(e)
        if teardown_errors:
            raise TeardownErrors(teardown_errors)

    def run(self, *args, **kwargs):
        try:
            return super(TestCase, self).run(*args, **kwargs)
        finally:
            self._exit()


def main(*args, **kwargs):
    unittest.main(*args, **kwargs)
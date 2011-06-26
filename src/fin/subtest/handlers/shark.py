
import os

import fin.util
import fin.subtest.handlers.unit


def slow_test_filter(test):
    if not isinstance(test, fin.subtest.handlers.unit.UnittestTest):
        return True
    base = os.path.abspath(test.filename)
    module = fin.util.import_module_by_filename(base)
    case = getattr(module, test.case)
    setup = getattr(case, "setUp", None)
    if hasattr(setup, "slow_test"):
        return False
    method = getattr(case, test.method)
    if hasattr(method, "slow_test"):
        return False
    return True


def defaults():
    os.environ["RUNNING_TESTS"] = "1"
    return [slow_test_filter], []

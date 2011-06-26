# (C) Steve Stagg

import fnmatch
import os
import types
import traceback
import unittest

import fin.subtest.runner
import fin.subtest.handlers.path


class UnittestTest(fin.subtest.runner.Test): 

    FIELDS = ("module_name", "case", "method")

    def __init__(self, filename, case, method):
        self.filename = filename
        self.case = case
        self.method = method

    @property
    def module_name(self):
        return ".".join(fin.util.filename_to_module_name(self.filename))

    def standard_form(self):
        return "%s.%s.%s" % (self.module_name, self.case, self.method)


class UnittestCompatibleResult(object):

    IGNORE = set(["startTest", "stopTest"])

    def __init__(self, bus, test):
        self.bus = bus
        self.test = test

    # The following three methods are shamelessly copied from unittest2 :(
    def _is_relevant_tb_level(self, tb):
        return '__unittest' in tb.tb_frame.f_globals

    def _count_relevant_tb_levels(self, tb):
        length = 0
        while tb and not self._is_relevant_tb_level(tb):
            length += 1
            tb = tb.tb_next
        return length

    def format_tb(self, err, test):
        """Converts a sys.exc_info()-style tuple of values into a string."""
        exctype, value, tb = err
        # Skip test runner traceback levels
        while tb and self._is_relevant_tb_level(tb):
            tb = tb.tb_next
        if exctype is test.failureException:
            # Skip assert*() traceback levels
            length = self._count_relevant_tb_levels(tb)
            msgLines = traceback.format_exception(exctype, value, tb, length)
        else:
            msgLines = traceback.format_exception(exctype, value, tb)
        return "".join(msgLines)

    def addSuccess(self, *args):
        self.bus.report_result(self.test, "success")

    def addError(self, test, err):
        self.bus.report_result(self.test, "error", self.format_tb(err, test))

    def addFailure(self, test, err):
        self.bus.report_result(self.test, "fail", self.format_tb(err, test))

    def addExpectedFailure(self, test, *args):
        self.bus.report_result(self.test, "expectedfail")

    def __getattr__(self, name):
        if name in self.IGNORE:
            return lambda *a, **k: None


class UnitFileTestHandler(fin.subtest.runner.TestRunner):

    TYPES = (fin.subtest.handlers.path.PathTest, )

    def __init__(self, method_prefix="test", 
                 case_class=unittest.TestCase,
                 file_match="*.py"):
        self.method_prefix = method_prefix
        self.case_class = case_class
        self.file_match = file_match

    def _handles(self, test):
        if not os.path.exists(test.path) or not os.path.isfile(test.path):
            return False
        return fnmatch.fnmatch(os.path.basename(test.path), self.file_match)

    def cases_from_module(self, module):
        for name in dir(module):
            obj = getattr(module, name)
            try:
                is_subclass = issubclass(obj, self.case_class)
            except TypeError:
                continue
            if is_subclass:
                yield name, obj

    def is_test_method(self, case, name):
        return (name.startswith(self.method_prefix) 
                and callable(getattr(case, name)))

    def run(self, bus, test):
        base = os.path.abspath(test.path)
        try:
            module = fin.util.import_module_by_filename(base)
        except Exception, e:
            msg = traceback.format_exc()
            bus.report_result(test, "error", "Unimportable Module", msg)
            return
        for case_name, case in self.cases_from_module(module):
            for method_name in dir(case):
                if self.is_test_method(case, method_name):
                    bus.found_test(
                        UnittestTest(test.path, case_name, method_name))


class UnittestHandler(fin.subtest.runner.TestRunner):
        
    TYPES = (UnittestTest, )
    
    def run(self, bus, test):
        base = os.path.abspath(test.filename)
        module = fin.util.import_module_by_filename(base)
        case = getattr(module, test.case)
        case(test.method).run(UnittestCompatibleResult(bus, test))
    

def defaults():
    return [], [UnitFileTestHandler(), UnittestHandler()]

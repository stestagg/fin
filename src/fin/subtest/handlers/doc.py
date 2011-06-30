# (C) Steve Stagg

import copy
import doctest
import fnmatch
import os
import types
import traceback

import fin.subtest.runner
import fin.subtest.handlers.path


class DoctestTest(fin.subtest.runner.Test):

    FIELDS = ("module_name", "case", "example")

    def __init__(self, filename, case, example=None):
        self.filename = filename
        self.case = case
        self.example = example

    @property
    def module_name(self):
        return ".".join(fin.util.filename_to_module_name(self.filename))

    def standard_form(self):
        if self.example is not None:
            return "%s.%s(%i)" % (self.module_name, self.case, self.example)
        return "%s.%s" % (self.module_name, self.case)


class DoctestFileTestHandler(fin.subtest.runner.TestRunner):

    TYPES = (fin.subtest.handlers.path.PathTest, )

    def __init__(self, method_prefix="test",
                 file_match="*.py"):
        self.method_prefix = method_prefix
        self.file_match = file_match

    def _handles(self, test):
        if not os.path.exists(test.path) or not os.path.isfile(test.path):
            return False
        return fnmatch.fnmatch(os.path.basename(test.path), self.file_match)

    def cases_from_module(self, module):
        for test in doctest.DocTestFinder().find(module):
            if len(test.examples) > 0:
                accessor = fin.string.ltrim(test.name, module.__name__)
                yield accessor.strip(".")

    def run(self, bus, test):
        base = os.path.abspath(test.path)
        try:
            module = fin.util.import_module_by_filename(base)
        except Exception, e:
            msg = traceback.format_exc()
            bus.report_result(test, "error", "Unimportable Module", msg)
            return
        for case in self.cases_from_module(module):
            bus.found_test(DoctestTest(test.path, case))


class DocTestRunner(doctest.DocTestRunner):

    def __init__(self, bus, test):
        doctest.DocTestRunner.__init__(self)
        self.bus = bus
        self.fin_test = test

    def format_tb(self, err):
        """Converts a sys.exc_info()-style tuple of values into a string."""
        exctype, value, tb = err
        msgLines = traceback.format_exception(exctype, value, tb)
        return "".join(msgLines)

    def report_start(self, out, test, example):
        new_test = copy.copy(self.fin_test)
        new_test.example = test.examples.index(example)
        if new_test.example > 0:
            self.bus.report_test(new_test)

    def report_success(self, out, test, example, got):
        new_test = copy.copy(self.fin_test)
        new_test.example = test.examples.index(example)
        self.bus.report_result(new_test, "success")

    def report_failure(self, out, test, example, got):
        new_test = copy.copy(self.fin_test)
        new_test.example = test.examples.index(example)
        self.bus.report_result(new_test, "fail",
                               "%s != %s" % (got.strip(), example.want.strip()))

    def report_unexpected_exception(self, out, test, example, exc_info):
        new_test = copy.copy(self.fin_test)
        new_test.example = test.examples.index(example)
        self.bus.report_result(new_test, "fail", self.format_tb(exc_info))


class DoctestHandler(fin.subtest.runner.TestRunner):

    TYPES = (DoctestTest, )

    def run(self, bus, test):
        base = os.path.abspath(test.filename)
        module = fin.util.import_module_by_filename(base)
        object = module
        for part in test.case.split("."):
            object = getattr(object, part)
        tests = doctest.DocTestFinder().find(object, module=module)
        runner = DocTestRunner(bus, test)
        for doc_test in tests:
            runner.run(doc_test)

def defaults():
    return [], [DoctestFileTestHandler(), DoctestHandler()]

# (C) Steve Stagg

import sys

import fin.bus
import fin.named
import fin.subtest.handlers.path


ResultType = fin.named.namedtuple("ResultType", "name", "code", "description")


class ResultHandler(fin.bus.Handler):

    LIMIT = 1
    STREAM = sys.stdout
    ALLOWED_RESULTS = set(["success", "fail", "error",
                           "expectedfail", "skip", "unhandled"])

    def __init__(self, stream=STREAM):
        self.stream = stream

    def output(self, title, *data):
        data = [str(item) for item in data]
        self.stream.write("\x1b[1m%s\x1b[0m\n%s\n" % (title, "\n".join(data)))

    def ignore_result(self, test, result):
        return False

    def error(self, bus, *messages):
        """ Non-test related errors """
        self.output("Unexpected Error", *messages)

    def output_result(self, test, result):
        self.stream.write("%r: %s\n" % (
                test, result))

    def report_result(self, bus, test, result, *data):
        assert result in self.ALLOWED_RESULTS, (
            "%r test result not understood" % (result, ))
        if self.ignore_result(test, result):
            return
        self.output_result(test, result)
        if len(data) > 0:
            title = (repr(test) if not hasattr(test, "standard_form")
                     else test.standard_form())
            self.output(title, *data)

    def report_test(self, bus, test):
        """This is here to signal that this handler understands these messages
        it just ignores them"""
        pass

    def report_start(self, bus, test):
        """This is here to signal that this handler understands these messages
        it just ignores them"""
        pass

    def report_stop(self, bus, test):
        """This is here to signal that this handler understands these messages
        it just ignores them"""
        pass

    def report_totals(self, bus):
        """This is here to signal that this handler understands these messages
        it just ignores them"""
        pass



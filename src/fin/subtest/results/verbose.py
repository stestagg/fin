# (C) Steve Stagg

"""
Similar to the unittest verbose output
"""

import struct
import fcntl
import termios
import time

import fin.color
import fin.subtest.resultbase
import fin.subtest.handlers.path

C = fin.color.C


class Handler(fin.subtest.resultbase.ResultHandler):

    DESCRIPTIONS = {
        "success": ("ok", "ok", C.green),
        "fail": ("FAIL", "failures", C.red),
        "error": ("ERROR", "errors", C.red),
        "expectedfail": ("Expected Failure",
                         "expected failures", C.yellow),
        "skip": ("SKIP", "Skipped", C.blue),
        "unhandled": ("UNHANDLED", "Unhandled", C.red.bold),
        }

    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        self.first_output = None
        self.last_output = None
        self.total = 0
        self.counts = dict((name, 0) for name in self.DESCRIPTIONS.keys())

    def ignore_result(self, test, result=None):
        return isinstance(test, fin.subtest.handlers.path.PathTest)

    def output(self, data):
        for part in data:
            self.stream.write("%s\n" % str(part))

    def report_result(self, bus, test, result, *data):
        assert result in self.ALLOWED_RESULTS, (
            "%r test result not understood" % (result, ))
        if self.ignore_result(test, result):
            return
        description = (test.standard_form() if hasattr(test, "standard_form")
                       else repr(test))
        result_text, _, color= self.DESCRIPTIONS[result]
        message = "%s ... %s" % (description, color(result_text))
        self.output([message])
        self.counts[result] += 1
        if len(data) > 0:
            self.output(
                ("", "=" * 60,
                "%s: %s" % (result_text, description),
                "-" * 60,
                ) +
                tuple(data) + ("-" * 60, ))

    def report_start(self, bus, test):
        if self.first_output is None:
            self.first_output = time.time()

    def report_stop(self, bus, test):
        self.last_output = time.time()

    def report_test(self, bus, test):
        if not self.ignore_result(test):
            self.total += 1

    def report_totals(self, bus):
        self.stream.write("-" * 60)
        message = "Ran %s tests in %s seconds" % (
            C.bold(str(self.total)), C.bold(
                "%.3f" % (self.last_output - self.first_output)))
        self.stream.write("\n%s\n" % message)
        any_failed = any([self.counts[c] for c in
            ["error", "fail", "unhandled"]])
        status = "FAILED" if any_failed else "OK"
        counts = []
        for type, count in self.counts.items():
            if count == 0 or type == "success":
                continue
            _, description, _ = self.DESCRIPTIONS[type]
            counts.append("%s=%i" % (description, count))
        if len(counts) > 0:
            self.stream.write("%s (%s)\n" % (status, ", ".join(counts)))
        else:
            self.stream.write("%s\n" % status)
# (C) Steve Stagg

"""
Like `basic` but with more info about the test start/stop
"""

import fin.subtest.resultbase


class Handler(fin.subtest.resultbase.ResultHandler):

    def report_start(self, bus, test):
        self.stream.write("Starting: %r\n" % (test, ))

    def report_stop(self, bus, test):
        self.stream.write("Stopping: %r\n" % (test, ))

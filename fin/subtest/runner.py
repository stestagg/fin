# (C) Steve Stagg

import functools
import os
import traceback

import fin.bus
import fin.util
import fin.named


class SubtestBus(fin.bus.Bus):

    MESSAGE_TYPES = (
        "found_test", 
        "add_test",
        "report_test",
        "report_result",
        "report_start",
        "report_stop",
        "report_totals",
        "error")


class Test(object): 

    FIELDS = NotImplemented

    def __repr__(self):
        args = ", ".join(repr(getattr(self, field)) for field in self.FIELDS)
        return "%s(%s)" % (type(self).__name__, args)


def bus_exception(fun):
    @functools.wraps(fun)
    def wrapped(self, bus, *args, **kwargs):
        try:
            fun(self, bus, *args, **kwargs)
        except Exception, e:
            msg = traceback.format_exc()
            bus.error("Uncaught exception in test handler:\n%s" % msg)
            raise
    return wrapped


class TestCaseHandler(fin.bus.Handler):

    def __init__(self, filters, runners):
        self.runners = runners
        self.filters = filters
        
    @bus_exception
    def found_test(self, bus, test):
        assert isinstance(test, Test)
        for filter_ in self.filters:
            if not filter_(test):
                bus.report_result(test, "skip")
                return
        bus.add_test(test)
        bus.report_test(test)

    @bus_exception
    def add_test(self, bus, test):
        assert isinstance(test, Test)
        handled = False
        for runner in self.runners:
            if runner.handles(test):
                bus.report_start(test)
                runner.run(bus, test)
                bus.report_stop(test)
                handled = True
        if not handled:
            return bus.report_result(test, "unhandled")


class TestRunner(object):
    
    TYPES = ()

    def handles(self, test):
        if type(test) in self.TYPES:
            return self._handles(test)
        return False

    def _handles(self, test):
        return True

    def run(self, bus, test):
        raise NotImplementedError("%r does not implement 'run'" % (self, ))

    
    

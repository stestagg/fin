# (C) Steve Stagg

import collections
import sys

import fin.color


class Log(object):

    """A logging context manager"""
    LOGS = collections.defaultdict(list)

    def __init__(self, message,
                 ok_msg=None,
                 fail_msg=None,
                 stream=sys.stdout):
        self.message = message
        self.stream = stream
        color = fin.color.auto_color(stream)
        self.ok_msg = color.green.bold("OK") if ok_msg is None else ok_msg
        self.fail_msg = (color.red.bold("FAIL") if fail_msg is None
                         else fail_msg)
        self.has_child = False
        self.level = None

    @property
    def stack(self):
        return self.LOGS[self.stream]

    def enter_message(self, suffix=""):
        prefix = "| " * self.level
        return "%s%s: %s" % (prefix, self.message, suffix)

    def child_added(self, child):
        if not self.has_child:
            self.stream.write("\n")
        self.has_child = True

    def on_enter(self):
        self.stream.write(self.enter_message())
        self.stream.flush()

    def on_exit(self, failed):
        if self.has_child:
            self.stream.write(("| " * self.level) + "`- ")
        if failed:
            self.stream.write(self.fail_msg + "\n")
        else:
            self.stream.write(self.ok_msg + "\n")

    def __enter__(self):
        self.level = len(self.stack)
        for item in self.stack:
            item.child_added(self)
        self.on_enter()
        self.stack.append(self)

    def __exit__(self, exc_type, exc_value, tb):
        self.stack.remove(self)
        self.on_exit(exc_type is not None)


class CLog(Log):

    def on_enter(self):
        pass

    def child_added(self, child):
        if self.has_child or isinstance(child, CLog):
            return
        self.stream.write(self.enter_message("\n"))
        self.has_child = True

    def on_exit(self, failed):
        if not failed and not self.has_child:
            return
        if failed:
            for log in self.stack:
                log.child_added(None)
            self.child_added(None)
        return super(CLog, self).on_exit(failed)


# (C) Steve Stagg
# -*- coding: utf-8 -*-

import collections
import pprint
import sys
import functools
import textwrap

import fin.terminal
import fin.color

THEMES = {
    "default": {
        "OK": lambda C: C.green.bold("OK"),
        "FAIL": lambda C: C.red.bold("FAIL"),
        "CHILD_PADD": lambda C: "| ",
        "LAST_LINE": lambda C: "`- ",
        "OUTPUT_PREFIX": lambda C: "+",
    },
    "aa": {
        "OK": lambda C: C.green.bold("OK"),
        "FAIL": lambda C: C.red.bold("FAIL"),
        "CHILD_PADD": lambda C: C.purple("│ "),
        "LAST_LINE": lambda C: C.purple("└ "),
        "OUTPUT_PREFIX": lambda C: C.purple("▻"),
    },
    "mac": {
        "OK": lambda C: C.green.bold("✓"),
        "FAIL": lambda C: C.red.bold("✗"),
        "CHILD_PADD": lambda C: C.purple("│ "),
        "LAST_LINE": lambda C: C.purple("└ "),
        "OUTPUT_PREFIX": lambda C: C.purple.bold("▻"),  
    }
}


class ColorFakeDict(object):

    def __init__(self, color, items):
        self.color = color
        self.items = items

    def __getitem__(self, name):
        return self.color.blue.bold(self.items[name])


class LeaveLogException(BaseException):

    def __init__(self, msg):
        self.exit_msg = msg


class Log(object):

    """A logging context manager"""
    LOGS = collections.defaultdict(list)

    def __init__(self, message,
                 ok_msg=None,
                 fail_msg=None,
                 theme="default",
                 stream=sys.stderr):
        self.message = message
        self.theme = theme
        self.open = False
        self.stream = stream
        self.color = fin.color.auto_color(stream)
        self.ok_msg = self._theme_item("OK") if ok_msg is None else ok_msg
        self.fail_msg = (self._theme_item("FAIL") if fail_msg is None else fail_msg)
        self.has_child = False
        self.level = None

    def _theme_item(self, item, color=None):
        if color is None:
            color = self.color
        return THEMES[self.theme][item](color)

    @property
    def stack(self):
        return self.LOGS[self.stream]

    def enter_message(self, suffix=""):
        prefix = self._theme_item("CHILD_PADD") * self.level
        return "%s%s: %s" % (prefix, self.message, suffix)

    def child_added(self, child):
        if not self.has_child:
            self.stream.write("\n")
        self.has_child = True

    def on_enter(self):
        self.open = True
        self.stream.write(self.enter_message())
        self.stream.flush()

    def on_exit(self, failed, msg=None):
        if self.has_child:
            line = (self._theme_item("CHILD_PADD") * self.level
                    + self._theme_item("LAST_LINE"))
            self.stream.write(line)
        if msg is not None:
            self.stream.write(msg+ "\n")
        elif failed:
            self.stream.write(self.fail_msg + "\n")
        else:
            self.stream.write(self.ok_msg + "\n")
        self.open = False

    def exit(self, msg):
        raise LeaveLogException(msg)

    def __enter__(self):
        self.level = len(self.stack)
        for item in self.stack:
            item.child_added(self)
        self.on_enter()
        self.stack.append(self)
        return self

    def __exit__(self, exc_type, exc_value, tb):
        rv = None
        msg = None
        self.stack.remove(self)
        if exc_type is not None and issubclass(exc_type, LeaveLogException):
            rv = True
            msg = exc_value.exit_msg
        self.on_exit(exc_type is not None, msg)
        return rv

    def output(self, msg):
        if not self.open:
            raise ValueError("Cannot log output from outside log context.")
        self.child_added(None)
        for line in msg.splitlines():
            line = line.rstrip()
            if isinstance(line, unicode):
                line = line.encode("utf-8")
            full = "%s%s %s\n" % (
                self._theme_item("CHILD_PADD") * (self.level + 1), 
                self._theme_item("OUTPUT_PREFIX"),
                line)
            self.stream.write(full)
        self.stream.flush()

    def format(self, msg, **kwargs):
        if not self.open:
            raise ValueError("Cannot log output from outside log context.")
        if not isinstance(msg, basestring):
            msg = pprint.pformat(msg)
        if len(kwargs):
            msg = msg % ColorFakeDict(self.color, kwargs)
        cols, rows = fin.terminal.terminal_size()
        plain_prefix = (self._theme_item("CHILD_PADD", fin.color.NoColor()) * (self.level + 1) 
                        + self._theme_item("OUTPUT_PREFIX", fin.color.NoColor()))
        plain_prefix = plain_prefix.decode("utf-8")
        prefix_len = len(plain_prefix)
        remaining = cols - prefix_len - 1
        if remaining < 0:
            remaining = 60
        for line in textwrap.wrap(msg, remaining, replace_whitespace=False):
            self.output(line)


class CLog(Log):

    def on_enter(self):
        pass

    def child_added(self, child):
        if self.has_child or isinstance(child, CLog):
            return
        self.stream.write(self.enter_message("\n"))
        self.has_child = True

    def on_exit(self, failed, msg=None):
        if not failed and not self.has_child:
            return
        if failed:
            for log in self.stack:
                log.child_added(None)
            self.child_added(None)
        return super(CLog, self).on_exit(failed, msg)


def logger(**kwargs):
    return functools.partial(Log, **kwargs)
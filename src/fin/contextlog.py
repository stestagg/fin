# (C) Steve Stagg
# -*- coding: utf-8 -*-

import collections
import io
import functools
import pprint
import sys
import textwrap
import types

import fin.terminal
import fin.color
import fin.duplex


THEMES = {
    "plain": {
        "OK": lambda C: C.green.bold("OK"),
        "FAIL": lambda C: C.red.bold("FAIL"),
        "CHILD_PADD": lambda C: "| ",
        "LAST_LINE": lambda C: "`- ",
        "OUTPUT_PREFIX": lambda C: "+",
        "START": lambda C, l: l
    },
    "aa": {
        "OK": lambda C: C.green.bold("OK"),
        "FAIL": lambda C: C.red.bold("FAIL"),
        "CHILD_PADD": lambda C: C.purple("│ "),
        "LAST_LINE": lambda C: C.purple("└ "),
        "OUTPUT_PREFIX": lambda C: C.purple("▻"),
        "START": lambda C, l: l
    },
    "mac": {
        "OK": lambda C: C.green.bold(u"✓"),
        "FAIL": lambda C: C.red.bold(u"✗"),
        "CHILD_PADD": lambda C: C.purple(u"│ "),
        "LAST_LINE": lambda C: C.purple(u"╰ "),
        "OUTPUT_PREFIX": lambda C: C.purple.bold(u"▻"),
        "START": lambda C, l: C.purple.bold(l)
    },
}


class ColorFakeDict(object):

    def __init__(self, color, items):
        self.color = color
        self.items = items

    def __getitem__(self, name):
        return self.color.blue.bold(str(self.items[name]))


class LeaveLogException(BaseException):

    def __init__(self, msg):
        self.exit_msg = msg


def find_open_log(cls):
    for stack in cls.LOGS.values():
        if len(stack) > 0:
            return stack[-1]
    raise ValueError("Cannot find a suitable context log to output to")

DEFAULT_STREAM = sys.stderr
if hasattr(sys.stderr, "buffer"):
    DEFAULT_STREAM = sys.stderr.buffer.raw

class Log(object):

    """A logging context manager that provides easy to understand, and useful console output.

    Multiple logs may be nested (provided they use the same output stream) and
    the output reflects this, allowing for complex processing to be reflected simply to the user

    :Example:

    >>> from fin.contextlog import Log

    >>> def do_stuff():
    >>>     with Log("Doing stuff"):
    >>>         pass

    :param message: A string to be output when the context manager is entered
    :param ok_msg: Defaults to the theme-specific 'OK' message.
                    The string that is printed if the Context manager exits without error
    :param fail_msg: Defaults to the theme-specific 'Fail' message.
                    The string that is printed if the Context manager detects an exception
    :param theme: contextlib has several themes that control how the output is displayed, common ones are 'default', 'aa', and 'mac'
                    Note, for performance reasons, themes cannot be mixed on the same stream.
    :param stream:  A file-like object (default is stderr) that the context output is written to.

     """
    LOGS = collections.defaultdict(list)

    def __init__(self, message,
                 ok_msg=None,
                 fail_msg=None,
                 theme="mac",
                 stream=DEFAULT_STREAM):
        self.message = message
        self.theme = theme
        self.open = False
        self.stream = stream
        if isinstance(self.stream, io.TextIOBase):
            try:
                unicode
            except NameError:
                self.stream_encoder = lambda x: x
            else:
                self.stream_encoder = lambda x: unicode(x)
        else:
            self.stream_encoder = lambda x: x.encode('utf-8', errors='replace')

        self.color = fin.color.auto_color(stream)
        self.ok_msg = self._theme_item("OK") if ok_msg is None else ok_msg
        self.fail_msg = (self._theme_item("FAIL") if fail_msg is None else fail_msg)
        self.has_child = False
        self.level = None

    def _theme_item(self, item, color=None, *args):
        if color is None:
            color = self.color
        return THEMES[self.theme][item](color, *args)

    @property
    def stack(self):
        return self.LOGS[self.stream]

    def enter_message(self, suffix=""):
        prefix = self._theme_item("CHILD_PADD") * self.level
        message = self._theme_item("START", self.color, self.message)
        return u"%s%s: %s" % (prefix, message, suffix)

    def _write(self, data):
        self.stream.write(self.stream_encoder(data))

    def child_added(self, child):
        if not self.has_child:
            self._write("\n")
        self.has_child = True

    def on_enter(self):
        self.open = True
        self._write(self.enter_message())
        self.stream.flush()

    def on_exit(self, failed, msg=None):
        if self.has_child:
            line = (self._theme_item("CHILD_PADD") * self.level
                    + self._theme_item("LAST_LINE"))
            self._write(line)
        if msg is not None:
            self._write(msg+ "\n")
        elif failed:
            self._write(self.fail_msg + "\n")
        else:
            self._write(self.ok_msg + "\n")
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
        while self.stack and self.stack[-1] != self:
            self.stack[-1].__exit__(None, None, None)
        self.stack.remove(self)
        if exc_type is not None and issubclass(exc_type, LeaveLogException):
            rv = True
            msg = exc_value.exit_msg
        self.on_exit(exc_type is not None, msg)
        return rv

    @fin.duplex.method(inst_lookup_fun=find_open_log)
    def output(self, msg):
        """
        Output `msg` to the stream, but correctly indented
        to fit nicely within the current contextlog output.

        :param msg: String to be output to the stream
        """
        if isinstance(self, type) and issubclass(self, Log):
            for stack in self.LOGS.viewvalues():
                if len(stack) > 0:
                    self = stack[-1]
                    break
            else:
                raise ValueError("Cannot find a suitable context log to output to")
        if not self.open:
            raise ValueError("Cannot log output from outside log context.")
        self.child_added(None)
        for line in msg.splitlines():
            line = line.rstrip()
            full = "%s%s %s\n" % (
                self._theme_item("CHILD_PADD") * (self.level + 1),
                self._theme_item("OUTPUT_PREFIX"),
                line)
            self._write(full)
        self.stream.flush()

    @fin.duplex.method(inst_lookup_fun=find_open_log)
    def format(self, msg, *args, **kwargs):
        """
        As Log.output, but provides prettier output.  Using pformat, color-based substitution, and word wrapping.

        :param msg: If msg is a string, any args or kwargs are used in percent subsitutions,
                    with the subsitution values output in a different color.  log.format('user %s', user.name)
                    might  output '|+ user *bob*' (where bob is displayed in blue)
        :param msg: If msg is not a string, then pprint.pformat is called on it, and the result is output
        """
        if not self.open:
            raise ValueError("Cannot log output from outside log context.")
        if not isinstance(msg, str):
            msg = pprint.pformat(msg)
        elif args:
            msg = msg % tuple(self.color.blue.bold(str(a)) for a in args)
        elif kwargs:
            msg = msg % ColorFakeDict(self.color, args, kwargs)
        cols, rows = fin.terminal.terminal_size()
        plain_prefix = (self._theme_item("CHILD_PADD", fin.color.NoColor()) * (self.level + 1)
                        + self._theme_item("OUTPUT_PREFIX", fin.color.NoColor()))
        plain_prefix = plain_prefix
        prefix_len = len(plain_prefix)
        remaining = cols - prefix_len - 1
        if remaining < 0:
            remaining = 60
        for line in textwrap.wrap(msg, remaining, replace_whitespace=False):
            self.output(line)


class CLog(Log):
    """A logging context manager, similar to :class:`fin.contextlog.Log`, that only produces output if an exception occurs
        or log.output()/log.format() is called.

       This means that an app/script that uses CLog could run silently if there are no errors,
       but show all the context if/when an error does occur
    """

    def on_enter(self):
        self.open = True

    def child_added(self, child):
        if self.has_child or isinstance(child, CLog):
            return
        self._write(self.enter_message("\n"))
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

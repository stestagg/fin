
import os
import sys

import fin.string


class Color(object):
    """
    A simple class for producing pretty terminal output.  While :class:`Color` is abstract, :class:`VtColor` provides common 
    VT-100 (xterm) compatible output.  This is a very light, small library, and doesn't deal with curses or terminfo.

    The module global ``C`` is created at import time.  If standard out appears to support color output, then this will be
    an instance of :class:`VtColor`, otherwise, :class:`NoColor`.

    Typical Usage::

        c = fin.color.C
        print c.blue + "I'm blue, da-ba-dee da-ba-dai" + c.reset
        print c.red.bold("Color") + c.red.blue("Blind")
        print c.green("In") + c.bg_green.black("verse") # Note assumes a white-on-black color scheme.
    """

    def __init__(self, parts=()):
        self.parts = parts

    def __call__(self, *data):
        return self + "".join(data) + self.only_reset

    def __getattr__(self, name):
        return self[name]

    def __getitem__(self, name):
        raise NotImplemented("__getitem__")

    def __add__(self, other):
        if isinstance(other, Color):
            return self.__class__(self.parts + other.parts)
        return str(self) + other

    def __radd__(self, other):
        if isinstance(other, Color):
            return self.__class__(other.parts + self.parts)
        return other + str(self)

    def __str__(self):
        raise NotImplemented()


class NoColor(Color):

    def __getitem__(self, name):
        return self

    def __str__(self):
        return ""


class VtColor(Color):

    COLORS = ["black", "red", "green", "yellow",
              "blue", "purple", "cyan", "white"]
    FG_BASE = 30
    BG_BASE = 40
    EXTRA = {
        "bold": 1,
        "reset": 0,
    }

    def _get_value(self, name):
        name = name.lower()
        if name in self.EXTRA:
            return self.EXTRA[name]
        base = self.FG_BASE
        bg_name = fin.string.ltrim(name, "bg_", "background_", "b_")
        if bg_name != name:
            name = bg_name
            base = self.BG_BASE
        try:
            offset = self.COLORS.index(name)
        except ValueError:
            raise AttributeError(name)
        return base + offset

    def __getitem__(self, name):
        current_parts = self.parts
        only_name = fin.string.ltrim(name, "only_")
        if only_name != name:
            name = only_name
            current_parts = ()
        return VtColor(current_parts + (self._get_value(name), ))

    def __str__(self):
        data = ";".join("%i" % p for p in self.parts)
        return "\x1b[" + data + "m"


KNOWN_TERMINAL_TYPES = set([
    "linux", "term", "vt200"
])


def auto_color(stream=sys.stdin):
    """
    Depending on environment variables, and if :attr:`stream` is a tty, return a Color object that will output
    colored text, or one that outputs plain text.
    """
    term_name = os.environ.get("TERM", "").lower()
    if (stream.isatty()
        and (term_name in KNOWN_TERMINAL_TYPES or "xterm" in term_name)):
        return VtColor()
    return NoColor()


C = auto_color()


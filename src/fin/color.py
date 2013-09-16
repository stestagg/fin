
import os
import sys

import fin.string


class Color(object):
    """ An object for producing pretty terminal output.
    'Dial up' the correct codes by attribute access, then generate the relevant
    escape sequences, by co-ercing to string.  i.e.:  str(C.red.bold) will
    return the correct sequence for outputting bold, red text.
    Alternately, you could do:  C.red.bold("Foo") to return an object
    that, when printed, will output a bold, red Foo, then reset the terminal
    color state"""

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
    """Guess an return the relevant color class for the current environment,
       Note this doesn't use termcap or anything, yet, just does basic
       guesswork"""
    term_name = os.environ.get("TERM", "").lower()
    if (stream.isatty()
        and (term_name in KNOWN_TERMINAL_TYPES or "xterm" in term_name)):
        return VtColor()
    return NoColor()


C = auto_color()



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

    """
    A color class for when no color information should be output.  For example, if output can be redirected to a terminal
    OR a log file, NoColor can be transparently swapped in for the VtColor class to ensure that the data in the log file does
    not include a large number of escape codes.
    """

    def __getitem__(self, name):
        return self

    def __str__(self):
        return ""


class VtColor(Color):

    """
    The color class for VT-compatible terminals (basically all non-windows terminals).

    The color attributes may be used in two ways.  Getting a color is a matter of referencing the correct attribute::

        >>> C.red
        <fin.color.VtColor at 0x7f904012fb90>

    This may then be converted to a string, for printing::

        >>> str(C.red)
        '\\x1b[34m'
        >>> C.red + "foo" + C.reset
        '\\x1b[31mfoo\\x1b[0m'

    The alternate syntax is to `call` the color, passing in a string, which implicitly add the color code before the string, 
    and adds a reset afterwards (NOTE: the reset will reset all color information, including any inherited)::

        >>> C.red("hello") + C.blue("world")
        '\\x1b[31mhello\\x1b[0m\\x1b[34mworld\\x1b[0m'

    Printing any of the above in a standard (non-windows) terminal, will result in the correct colored output.

    The available colors are listed below.  All colors may be prefixed with 'bg_', and colors may be combined by further attribute access::

        >>> C.bg_blue.white.bold("Bold, white-on-blue text")
        '\\x1b[44;37;1mBold, white-on-blue text\\x1b[0m'

    Two special attributes:  'bold', and 'reset' respectively turn the text bold (or use bright colors, depending on console)
    and reset all color attributes.
    """

    COLORS = ["black", "red", "green", "yellow",
              "blue", "purple", "cyan", "white"]
    """ All colors that may be referenced """
    FG_BASE = 30
    BG_BASE = 40
    EXTRA = {
        "bold": 1,
        "reset": 0,
    }
    """ Non-color attributes """

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
    This does some simple tests to determine if the output stream supports colors, returning the corect Color class
    for the stream.

    The lookup is intentionally kept simple, as this has proved to capture 99% of cases without adding the burden 
    of more complicated capabilities databases.
    """
    term_name = os.environ.get("TERM", "").lower()
    if (stream.isatty()
        and (term_name in KNOWN_TERMINAL_TYPES or "xterm" in term_name)):
        return VtColor()
    return NoColor()


C = auto_color()
"""
An instance of :class:`Color` that is most appropriate for sys.stdout.  
Typically this will be a VtColor object, but when stdout is redirected to a file, or other non-terminal output
then it will revert to NoColor.

This constant allows code to simply refer to, for example::

    >>> fin.color.C.blue('hi')
    '\\x1b[34mhi\\x1b[0m'

"""

import os
import struct
import fcntl
import termios


def ioctl_GWINSZ(fd):
    """Ask the terminal directly what the window size is, Taken from
    http://stackoverflow.com/questions/566746/
    how-to-get-console-window-width-in-python"""
    try:
        cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
    except Exception, e:
        return None
    return cr


def terminal_size():
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        try:
            cr = (os.environ['LINES'], os.environ['COLUMNS'])
        except:
            cr = (25, 80)
    return int(cr[1]), int(cr[0])
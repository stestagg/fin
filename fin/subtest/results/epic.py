# (C) Steve Stagg

import struct
import fcntl
import termios
import time

import fin.color
import fin.subtest.resultbase
import fin.subtest.handlers.path

C = fin.color.C

def ioctl_GWINSZ(fd): 
    """Ask the terminal directly what the window size is, Taken from 
    http://stackoverflow.com/questions/566746/
    how-to-get-console-window-width-in-python"""
    try: 
        cr = struct.unpack(
            'hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
    except:
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
            cr = (env['LINES'], env['COLUMNS'])
        except:
            cr = (25, 80)
    return int(cr[1]), int(cr[0])


class Handler(fin.subtest.resultbase.ResultHandler):
    
    DESCRIPTIONS = {
        "success": ("OK", "OK", "OK", C.green),
        "fail": ("F", "Failure", "Failures", C.red),
        "error": ("E", "Error", "Errors", C.red),
        "expectedfail": ("x", "Expected Failure", 
                         "Expected Failures", C.yellow),
        "skip": ("s", "Skip", "Skipped", C.blue),
        "unhandled": ("u", "Unhandled", "Unhandled", C.red),
        }
    TYPES = {
        fin.subtest.handlers.path.PathTest: C.blue("D"), # D for discovery
        fin.subtest.handlers.unit.UnittestTest: C.green("t"),
        }

    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        self.first_output = None
        self.last_output = None
        self.total = 0
        self.counts = dict((name, 0) for name in self.DESCRIPTIONS.keys())
        self.running = []
        self.max_running = 0

    def ignore_result(self, test, result=None):
        return isinstance(test, fin.subtest.handlers.path.PathTest)

    def _runners(self):
        parts = []
        self.max_running = max(len(self.running), self.max_running)
        for run in self.running:
            char = self.TYPES.get(run, C.yellow("?"))
            parts.append(char)
        for i in range(self.max_running - len(parts)):
            parts.append(" ")
        return "[%s]" % ("".join(parts)), 2 + len(parts)

    def _ansii_encode(self, code):
        return "\x1b[%s" % code

    def format_counts(self, terse=False):
        parts = []
        char_count = 0
        total_name = "T" if terse else "Tests"
        char_count += len("%i %s" % (self.total, total_name))
        parts.append("%s %s" % (C.bold(str(self.total)), total_name))
        for name, count in self.counts.items():
            if count == 0:
                continue
            terse_desc, singular, plural, color = self.DESCRIPTIONS[name]
            if terse:
                desc = terse_desc
            elif count == 1:
                desc = singular
            else:
                desc = plural
            char_count += len(", %i %s" % (count, desc))
            parts.append(", " + color("%i %s" % (count, desc)))
        char_count += 1
        return "%s." % "".join(parts), char_count
                         
    def update(self):
        data = [self._ansii_encode("0G")]
        columns, rows = terminal_size()
        column = 0
        
        runners, runner_len = self._runners()
        data += runners
        data.append(" ")
        column += runner_len + 1
        
        counts, count_len = self.format_counts()
        if column + count_len > columns:
            counts, count_len = self.format_counts(terse=True)
        data.append(counts)
        column += count_len
        
        data.append(self._ansii_encode("K"))
        self.stream.write("".join(data))
        self.stream.flush()

    def output(self, data):
        self.stream.write(self._ansii_encode("0G") + self._ansii_encode("K"))
        for part in data:
            self.stream.write("%s\n" % str(part))

    def report_result(self, bus, test, result, *data):
        assert result in self.ALLOWED_RESULTS, (
            "%r test result not understood" % (result, ))
        if self.ignore_result(test, result):
            return
        self.counts[result] += 1
        if len(data) > 0:
            self.output(data)
        self.update()

    def report_start(self, bus, test):
        if self.first_output is None:
            self.first_output = time.time()
        self.running.append(type(test))
        self.update()

    def report_stop(self, bus, test):
        self.running.remove(type(test))
        self.last_output = time.time()
        self.update()

    def report_test(self, bus, test):
        if not self.ignore_result(test):
            self.total += 1
            self.update()

    def report_totals(self, bus):
        message = "Ran %s tests in %s seconds" % (
            C.bold(str(self.total)), C.bold(
                "%.2f" % (self.last_output - self.first_output)))
        self.stream.write("\n%s\n" % message)

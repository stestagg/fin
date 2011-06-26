# (C) Steve Stagg

import fin.subtest.resultbase
import fin.subtest.handlers.path


class Handler(fin.subtest.resultbase.ResultHandler):
    
    RESULT_CODES = {
        "success": ".", 
        "fail": "F",
        "error": "E",
        "expectedfail": "X",
        "skip": "s",
        "unhandled": "U",
        }

    def ignore_result(self, test, result):
        if result == "unhandled":
            return isinstance(test, fin.subtest.handlers.path.PathTest)
        return False

    def __init__(self, *args, **kwargs):
        super(Handler, self).__init__(*args, **kwargs)
        self.total = 0
        self.counts = dict((name, 0) for name in self.RESULT_CODES.keys())

    def output(self, title, *data):
        data = [str(item) for item in data]
        self.stream.write("\n\x1b[1m%s\x1b[0m\n%s\n" % (title, "\n".join(data)))

    def output_result(self, test, result):
        self.total += 1
        self.counts[result] += 1
        self.stream.write("%s" % self.RESULT_CODES[result])
        self.stream.flush()

    def report_totals(self, bus):
        message = ["Ran: %i tests" % self.total]
        for name, count in self.counts.items():
            if count > 0:
                message.append("%s: %i" % (name, count))
        self.stream.write("\n%s\n" % ", ".join(message))
        

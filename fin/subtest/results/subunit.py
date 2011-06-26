# (C) Steve Stagg

import fin.subtest.resultbase
import fin.subtest.handlers.path


class Handler(fin.subtest.resultbase.ResultHandler):
    
    MESSAGES = {
        "success": "success", 
        "fail": "failure",
        "error": "error",
        "expectedfail": "xfail",
        "skip": "skip",
        "unhandled": "error",
        }

    def ignore_result(self, test, result=None):
        if result in set(["fail", "error"]):
            return False
        return isinstance(test, fin.subtest.handlers.path.PathTest)

    def output(self, message, test, *data):
        # Paranoid output
        test_label = test.standard_form().replace("\n", " ")
        extra = ""
        if len(data) > 0:
            extra = [" ["]
            for part in data:
                if part.strip() == "]":
                    part = "]."
                extra.append(part.strip())
            extra.append("]")
            extra="%s" % "\n".join(extra)
        record = "%s: %s%s\n" % (message, test_label, extra)
        self.stream.write(record)

    def report_result(self, bus, test, result, *data):
        assert result in self.ALLOWED_RESULTS, (
            "%r test result not understood" % (result, ))
        if self.ignore_result(test, result):
            return
        message = self.MESSAGES[result]
        self.output(message, test, *data)

    def report_start(self, bus, test):
        if not self.ignore_result(test):
            self.output("test", test)

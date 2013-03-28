# (C) Cmed Ltd, 2011

"""%prog [paths ...]
Find and run tests below paths
"""

import os
import multiprocessing
import optparse
import sys

import fin.subtest.results
import fin.subtest.runner
import fin.subtest.handlers.path
import fin.subtest.handlers.doc
import fin.subtest.handlers.unit
import fin.subtest.handlers.shark
import fin.util


def parse_args(args):
    parser = optparse.OptionParser(usage=__doc__)
    parser.add_option("-j", dest="num_processes",
                      default=multiprocessing.cpu_count(),
                      metavar=multiprocessing.cpu_count(),
                      type=int, help="Run x processes")
    parser.add_option("-o", "--outputter", dest="outputter", default="epic",
                      help="Use the named outputter", metavar="epic")
    parser.add_option("-O", "--list-outputters", dest="list_outputters",
                      action="store_true", default=False,
                      help="List all available outputters, and do nothing else")
    options, args = parser.parse_args(args)
    options.args = args
    return options


def list_outputters():
    output_modules = fin.util.import_child_modules("fin", "subtest", "results")
    print fin.color.C.bold("Valid Outputters")
    print "-" * 16
    for name, module in sorted(output_modules.items()):

        doc = getattr(module, "__doc__", None)
        if doc is None:
            doc = "Undocumented"
        print fin.color.C.bold(name) + " - " + doc.strip()


def get_outputter(name):
    mod = fin.util.import_module_by_name_parts(
        "fin", "subtest", "results", name)
    return getattr(mod, "Handler")


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    options = parse_args(args)
    if options.list_outputters:
        list_outputters()
        return
    if len(options.args) == 0:
        options.args = ["."]

    # Shortcut:
    runners = []
    filters = []
    for module in [fin.subtest.handlers.path,
                   fin.subtest.handlers.unit,
                   fin.subtest.handlers.shark,
                   fin.subtest.handlers.doc]:
        new_filters, new_runners = module.defaults()
        runners.extend(new_runners)
        filters.extend(new_filters)
    outputter = get_outputter(options.outputter)()
    runner = fin.subtest.runner.TestCaseHandler(
        filters=filters, runners=runners)

    os.close(sys.stdin.fileno())
    sys.stdin.close()

    bus = fin.subtest.runner.SubtestBus([runner, outputter],
                                        options.num_processes)
    for arg in options.args:
        bus.found_test(fin.subtest.handlers.path.PathTest(arg))
    bus.join()
    bus.report_totals()
    bus.close()


if __name__ == '__main__':
    sys.exit(main())

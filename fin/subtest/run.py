# (C) Cmed Ltd, 2011

"""%prog [paths ...]
Find and run tests below paths
"""

import optparse
import sys

import fin.subtest.results
import fin.subtest.runner
import fin.subtest.handlers.path
import fin.subtest.handlers.unit
import fin.subtest.handlers.shark


def parse_args(args):
    parser = optparse.OptionParser(usage=__doc__)
    parser.add_option("-v", "--verbose", dest="verbosity", action="count",
                      default=0, help="Increase verbosity")
    parser.add_option("-j", dest="num_processes", 
                      default=multiprocessing.cpu_count(),
                      type=int, help="Run x processes")
    parser.add_option("-o", "--outputter", dest="outputter", default="terse",
                      help="Use the named outputter", metavar="terse")
    options, args = parser.parse_args(args)
    options.args = args
    return options


def get_outputter(name):
    mod = fin.util.import_module_by_name_parts(
        "fin", "subtest", "results", name)
    return getattr(mod, "Handler")


def main(args=None):
    if args is None:
        args = sys.argv[1:]
    options = parse_args(args)
    if len(options.args) == 0:
        options.args = ["."]
    
    # Shortcut:
    runners = []
    filters = []
    for module in [fin.subtest.handlers.path, 
                   fin.subtest.handlers.unit,
                   fin.subtest.handlers.shark]:
        new_filters, new_runners = module.defaults()
        runners.extend(new_runners)
        filters.extend(new_filters)
    outputter = get_outputter(options.outputter)()
    runner = fin.subtest.runner.TestCaseHandler(
        filters=filters,
        runners=runners)
    
    
    bus = fin.subtest.runner.SubtestBus([runner, outputter],
                                        options.num_processes)
    for arg in options.args:
        bus.found_test(fin.subtest.handlers.path.PathTest(arg))
    bus.join()
    bus.report_totals()
    bus.close()

    
if __name__ == '__main__':
    sys.exit(main())

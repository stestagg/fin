# (C) Steve Stagg, 2011

import sys

import fin.util
import fin.modelmapper.profiler

def dot(model_name):
    print "digraph model{"
    model = fin.util.get_fully_qualified_object(model_name)
    predicates, outputs = zip(*model.MODEL_MAP.keys())
    predicates = set(predicates)
    outputs = set(outputs)
    for node in predicates | outputs:
        color = ""
        if node in predicates:
            if node in outputs:
                color = '"#1978be"'
            else:
                color = "darkblue"
        else:
            color = "darkred"
        print "\t%s[fillcolor = %s,style=filled];" % (node, color)
    for predicate, output in model.MODEL_MAP.keys() :
        print "\t%s -> %s;" % (predicate, output)
    print "}"

def profile(method_name):
    with fin.modelmapper.profiler.profile():
        method = fin.util.get_fully_qualified_object(method_name)
        method()

def main(args):
    command = args[0]
    {"dot": dot,
     "profile": profile,
    }[command](*args[1:])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
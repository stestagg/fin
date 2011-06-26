# (C) Steve Stagg

import os

import fin.subtest.runner


class PathTest(fin.subtest.runner.Test): 
    
    FIELDS = ("path", )

    def __init__(self, path):
        self.path = path


class DirectoryHandler(fin.subtest.runner.TestRunner):

    TYPES = (PathTest, )

    def _handles(self, test):
        return os.path.isdir(test.path)

    def run(self, bus, test):
        base = os.path.abspath(test.path)
        for child in os.listdir(test.path):
            child_path = os.path.join(base, child)
            bus.found_test(PathTest(child_path))
        
        
def defaults():
    return [], [DirectoryHandler()]

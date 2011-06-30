
import collections
import contextlib
import operator
import time

import fin.color
import fin.modelmapper.map

PROFILES = collections.defaultdict(lambda : collections.defaultdict(list))


class ModelProfiler(fin.modelmapper.map.model):

    def time(self, instance, method):
        start = time.time()
        val = method(instance)
        end = time.time()
        return val, end - start

    def _try_resolve(self, instance):
        resolvers = [entry for entry in instance.MODEL_MAP
                     if self.is_relevant(entry)]
        have_value = False
        for predicate, output, method in resolvers:
            if self._has_value(instance, predicate):
                val, run_time = self.time(instance, method)
                self.__set__(instance, val)
                have_value = True
                PROFILES[type(instance)][(predicate, output)].append(run_time)
        return have_value


class MapTable(dict):

    def __init__(self, obj, maps):
        super(MapTable, self).__init__()
        self.predicates = set([a for a, _, _ in obj.MODEL_MAP])
        self.outputs = set([b for _, b, _ in obj.MODEL_MAP])
        for p in self.predicates:
            self[p] = dict((b, None) for b in self.outputs)

        for predicate, output, average_time in maps:
            self[predicate][output] = ((predicate, ), average_time)
        while self.fill_in_blank():
            pass

    def __getitem__(self, item):
        if isinstance(item, slice):
            assert item.step is None, "MapTable does not support a:b:c slices"
            if item.start is not None:
                if item.stop is not None:
                    return self[item.start][item.stop]
                return self[item.start]
            if item.stop is not None:
                return dict((p, self[p][item.stop]) for p in self.keys())
            return self.items()
        return super(MapTable, self).__getitem__(item)

    def fill_in_blank(self):
        for (p, o), t in self.iteritems():
# this prevents path optimization in some cases
#            if t is not None:
#                continue
            predicate_links = set(
                output for output, data in self[p:].items() if data is not None)
            output_links = set(
                pred for pred, data in self[:o].items() if data is not None)
            common_links = predicate_links & output_links
            if len(common_links) == 0:
                continue
            candidate = None
            for common_link in common_links:
                start_path, start_time = self[p:common_link]
                end_path, end_time = self[common_link:o]
                full_path = start_path + end_path
                full_time = start_time + end_time
                if candidate is None or candidate[1] > full_time:
                    candidate = (full_path, full_time)
            if t is None or candidate[1] < t[1]:
                self[p][o] = candidate
                return True
        return False

    def dump(self):
        final_map = dict()
        for output in self.outputs:
            results = sorted([v for v in self[:output].values()
                              if v is not None], key=operator.itemgetter(1))
            final_map[output] = [v for v,t in results]
        return final_map

    def items(self):
        return list(self.iteritems())

    def iteritems(self):
        for predicate, maps in super(MapTable, self).iteritems():
            for output, data in maps.iteritems():
                if predicate == output:
                    continue
                yield (predicate, output), data


def serialise_results():
    for obj, maps in PROFILES.iteritems():
        print fin.color.C.blue.bold(str(obj))
        # First, check that all maps have been followed:
        measured_maps = set(maps.keys())
        all_maps = set([(a, b) for a, b, _ in obj.MODEL_MAP])
        missed_maps = all_maps - measured_maps
        if len(missed_maps) > 0:
            print fin.color.C.yellow.bold(
                "WARNING: not all maps were profiled.  Missing maps: %r" %
                (list(missed_maps), ))
        #get the averages and normalise
        average_maps = [(a, b, sum(c)/len(c)) for (a, b), c in maps.iteritems()]
        lowest_time = min(c for a, b, c in average_maps)
        average_maps = [(a, b, c/lowest_time) for a, b, c in average_maps]
        table = MapTable(obj, average_maps)
    import pprint
    pprint.pprint(table.dump())


@contextlib.contextmanager
def profile():
    old_model = fin.modelmapper.map.model
    fin.modelmapper.map.model = ModelProfiler
    yield
    fin.modelmapper.map.model = old_model
    resolvers = collections.defaultdict(list)
    serialise_results()
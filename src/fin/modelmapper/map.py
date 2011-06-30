# (C) Steve Stagg

import collections


class Mapped(object):

    ABSENCE_MARKER = None
    MODEL_MAP = NotImplemented
    ORDERED_MAPPINGS = NotImplemented
    _MAP_VALUES = None

    def __init__(self):
        self._MAP_VALUES = collections.defaultdict(
            lambda : self.ABSENCE_MARKER)


class UnresolvableProperty(Exception): pass


class model(object):

    def __init__(self, name):
        self.name = name

    def is_relevant(self, map_entry):
        predicate, outcome, method = map_entry
        return outcome == self.name

    def _get_value(self, instance, name=None):
        if name is None:
            name = self.name
        return instance._MAP_VALUES.get(name, instance.ABSENCE_MARKER)

    def _has_value(self, instance, name=None):
        return self._get_value(instance, name) != instance.ABSENCE_MARKER

    def _run_method(self, instance, predicate, output):
        value = instance.MODEL_MAP[(predicate, output)](instance)
        self.__set__(instance, value, output)
        return value

    def _try_resolve(self, instance):
        for path in instance.ORDERED_MAPPINGS[self.name]:
            if not self._has_value(instance, path[0]):
                continue
            for predicate, output in zip(path, path[1:]):
                self._run_method(instance, predicate, output)
            self._run_method(instance, path[-1], self.name)
            return True
        return False

    def __get__(self, instance, owner):
        if self._has_value(instance):
            return self._get_value(instance)
        self._try_resolve(instance)
        if self._has_value(instance):
            return self._get_value(instance)
        raise UnresolvableProperty(self.name)

    def __set__(self, instance, value, name=None):
        name = self.name if name is None else name
        instance._MAP_VALUES[name] = value

    def __del__(self, instance):
        del instance._MAP_VALUES[self.name]


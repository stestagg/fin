
from __future__ import with_statement

import ConfigParser
import os

try:
    import json
except ImportError:
    pass

import fin.cache


NOT_SET = object()


class TypedConfig(object):

    TRUTH_VALUES = frozenset(["yes", "t", "true", "1", "y", "on"])
    TYPE_PARSERS = {
        bool: lambda self, y: self._to_bool(y),
    }

    def _to_bool(self, value):
        return value.lower() in self.TRUTH_VALUES

    def get_typed(self, type_spec, keys, default=None):
        assert len(keys) > 0
        parser = type_spec
        if type_spec in self.TYPE_PARSERS:
            parser = lambda x: self.TYPE_PARSERS[type_spec](self, x)
        value = self.get(keys, NOT_SET)
        if value is NOT_SET:
            return default
        return parser(value)


class ConfigSource(object):

    def __getitem__(self, keys):
        if isinstance(keys, basestring):
            keys = keys.split(".")
        rv = self.get_value(*keys)
        if rv is NOT_SET:
            raise KeyError(keys)
        return rv

    def __iter__(self):
        return iter(self.get_keys())

    def __len__(self):
        return len(self.get_keys())

    def get(self, keys, default=None):
        if isinstance(keys, basestring):
            keys = keys.split(".")
        rv = self.get_value(*keys)
        return default if rv is NOT_SET else rv

    def get_keys(self, *parents):
        """Return a collection of all keys that have the specified parent keys."""
        raise NotImplementedError()

    def get_value(self, *keys):
        """ Given a particular multi-part key, return the corresponding value"""
        raise NotImplementedError()


class EnvironSource(ConfigSource):

    def __init__(self, prefix, sep="."):
        self.prefix = prefix
        self._sep = sep

    def _convert_keys(self, keys):
        return (self._sep.join((self.prefix, ) + keys)).upper()

    def get_value(self, *keys):
        return os.environ.get(self._convert_keys(keys), NOT_SET)

    def get_keys(self, *parents):
        prefix = self._convert_keys(parents) + self._sep
        prefix_len = len(prefix)
        return frozenset(k[prefix_len:].split(self._sep, 1)[0].lower()
                         for k in os.environ.keys() if k.startswith(prefix))


class ConfigParserSource(ConfigSource):

    def __init__(self, filename):
        self.filename = filename

    @fin.cache.property
    @fin.cache.depends("filename")
    def _parser(self):
        parser = ConfigParser.RawConfigParser()
        parser.read(self.filename)
        return parser

    def _find_sections(self, name):
        test = name.lower()
        return set([n for n in self._parser.sections() if n.lower() == test])

    def _find_keys(self, section, parts):
        prefix = ".".join(parts).lower() + "." if len(parts) else ""
        options = self._parser.options(section)
        prefix_len = len(prefix)
        # config parser by default lower-cases options for us
        return set([o[prefix_len:] for o in options if o.lower().startswith(prefix)])

    def get_value(self, *keys):
        key = ".".join(keys).lower()
        if self._parser.has_section(".") and self._parser.has_option(".", key):
            return self._parser.get(".", key)
        if len(keys) > 1:
            section_name = keys[0]
            section_key = ".".join(keys[1:]).lower()
            for section in self._find_sections(section_name):
                if self._parser.has_option(section, section_key):
                    return self._parser.get(section, section_key)
        return NOT_SET

    def get_keys(self, *parents):
        matching = set()
        if len(parents) > 0:
            sections = self._find_sections(parents[0])
            for section in sections:
                matching.update(self._find_keys(section, parents[1:]))
        else:
            matching.update([s.lower() for s in self._parser.sections() if s != "."])
        if self._parser.has_section("."):
            matching.update(self._find_keys(".", parents))
        return frozenset(m.split(".", 1)[0] for m in matching)


class DictSource(ConfigSource):

    def __init__(self, data):
        self.data = data

    def _find(self, keys):
        current = self.data
        for key in keys:
            key = key.lower()
            if not isinstance(current, dict):
                return NOT_SET
            for option in current.keys():
                if option.lower() == key:
                    break
            else:
                return NOT_SET
            current = current[option]
        return current

    def get_value(self, *keys):
        base = self._find(keys)
        if base is NOT_SET or isinstance(base, dict):
            return NOT_SET
        return str(base)

    def get_keys(self, *parents):
        base = self._find(parents)
        if isinstance(base, dict):
            return frozenset(k.lower() for k in base.keys())
        return frozenset()


class JSONSource(DictSource):

    def __init__(self, filename, data=None):
        if data is not None:
            self.data = lambda x: self.json.loads(data)
        self.filename = filename

    @property
    def json(self):
        try:
            return json
        except NameError:
            raise RuntimeError("No JSON libary available")

    @fin.cache.property
    @fin.cache.depends("filename")
    def data(self):
        if not os.path.exists(self.filename):
            return {}
        with open(self.filename) as fp:
            return self.json.load(fp)


class MultiSource(ConfigSource):

    def __init__(self, sources):
        self.sources = tuple(reversed(sources))

    def get_value(self, *keys):
        for source in self.sources:
            val = source.get_value(*keys)
            if val is not NOT_SET:
                return val
        return NOT_SET

    def get_keys(self, *parents):
        keys = set()
        for source in self.sources:
            keys.update(source.get_keys(*parents))
        return keys


class Config(MultiSource, TypedConfig):

    def __init__(self, name):
        self.name = name

    @fin.cache.property
    @fin.cache.depends("name")
    def sources(self):
        config_name = "%s.conf" % self.name
        xdg_path = os.environ.get("XDG_CONFIG_HOME",
                                  os.path.expanduser("~/.config"))
        user_config_path = os.path.join(xdg_path, config_name)
        system_config_path = os.path.join("/etc/%s" % config_name)
        return (EnvironSource(self.name, sep="_"),
                ConfigParserSource(user_config_path),
                ConfigParserSource(system_config_path))

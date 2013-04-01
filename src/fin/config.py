
from __future__ import with_statement

import ConfigParser
import os

import fin.cache


NOT_SET = object()


class ConfigSource(object):

    def __getitem__(self, keys):
        if isinstance(keys, basestring):
            keys = keys.split(".")
        rv = self.get_value(*keys)
        if rv is NOT_SET:
            raise KeyError(keys)
        return rv

    def get(self, keys, default=None):
        if isinstance(keys, basestring):
            keys = keys.split(".")
        rv = self.get_value(*keys)
        return default if rv is NOT_SET else rv

    def get_keys(self, *parents):
        raise NotImplementedError()

    def get_value(self, *keys):
        raise NotImplementedError()


class EnvironSource(ConfigSource):

    def __init__(self, prefix):
        self.prefix = prefix

    def _convert_keys(self, keys):
        return ("_".join((self.prefix, ) + keys)).upper()

    def get_value(self, *keys):
        key = ("_".join(keys)).upper()
        return os.environ.get(self._convert_keys(keys), NOT_SET)

    def get_keys(self, *parents):
        prefix = self._convert_keys(parents) + "_"
        prefix_len = len(prefix)
        return frozenset(k[prefix_len:].split("_", 1)[0].lower()
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
        return set([o[prefix_len:] for o in options if o.startswith(prefix)])

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
            if not isinstance(current, dict):
                return NOT_SET
            if key not in current:
                return NOT_SET
            current = current[key]
        return current

    def get_value(self, *keys):
        base = self._find(keys)
        if base is NOT_SET or isinstance(base, dict):
            return NOT_SET
        return str(base)

    def get_keys(self, *parents):
        base = self._find(parents)
        if isinstance(base, dict):
            return frozenset(base.keys())
        return frozenset()


class JSONSource(DictSource):

    def __init__(self, filename):
        self.filename = filename

    @fin.cache.property
    @fin.cache.depends("filename")
    def data(self):
        if not os.path.exists(self.filename):
            return {}
        with open(self.filename) as fp:
            return json.load(fp)


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


class Config(MultiSource):

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
        return (
            EnvironSource(self.name),
            ConfigParserSource(user_config_path),
            ConfigParserSource(system_config_path),
            )


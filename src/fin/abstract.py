import inspect
import os

import fin.module


def iter_subclasses(base):
    yield base
    for child in base.__subclasses__():
        for sub in iter_subclasses(child):
            yield sub


def get_base(cls):
    mro = cls.mro()
    class_index = mro.index(Class)
    if class_index == 0:
        raise AttributeError("type_by_name cannot be called on 'fin.abstract.Class'")
    return mro[class_index - 1]


class Class(object):

    NAME = NotImplemented

    @classmethod
    def all_types(cls, filter_fn=None):
        base_type = get_base(cls)
        if filter_fn is None:
            return tuple(iter_subclasses(base_type))
        return tuple(sub for sub in iter_subclasses(base_type) if filter_fn(sub))

    @classmethod
    def all_types_with_name(cls):
        return cls.all_types(lambda x: getattr(x, "NAME", NotImplemented) is not NotImplemented)

    @classmethod
    def type_by_name(cls, name):
        matching = cls.all_types(lambda x: getattr(x, "NAME", None) == name)
        if len(matching) == 0:
            raise KeyError(name)
        if len(matching) > 1:
            raise Exception("Multiple subclasses found with NAME: %s" % (name, ))
        return matching[0]


    @classmethod
    def load_subclasses(cls, dir_name=None, path=None):
        if path is None:
            base_class = get_base(cls)
            mod_path = inspect.getfile(base_class)
            if mod_path is None:
                raise Exception("Cannot find path for Abstract class %s" % (base_class))
            mod_dir = os.path.abspath(os.path.dirname(mod_path))
            subdir_name = (base_class.__name__.lower() + "s") if dir_name is None else dir_name
            path = os.path.join(mod_dir, subdir_name)
        parts = fin.module.path_to_module_parts(path, auto_add=True)
        fin.module.import_child_modules(parts)

# (C) Steve Stagg

import imp
import os
import os.path
import sys

import fin.string

PY_EXTENSIONS = [ext for ext, _, _ in imp.get_suffixes()]


def filename_to_module_name(path):
    path = os.path.abspath(path)
    sys_paths = set(os.path.abspath(path) for path in sys.path)
    module_path = fin.string.rtrim(path, *PY_EXTENSIONS)
    base_path = module_path
    while True:
        base_path = os.path.dirname(base_path)
        if base_path in sys_paths:
            break
        if os.path.dirname(base_path) == base_path:
            return None
    relative_path = module_path[len(base_path):].strip(os.path.sep)
    if "." in relative_path:
        return None
    return relative_path.split(os.path.sep)


def import_module_by_name_parts(*parts):
    __import__(".".join(parts))
    base = sys.modules[parts[0]]
    for part in parts[1:]:
        base = getattr(base, part)
    return base


def import_module_by_filename(path):
    parts = filename_to_module_name(path)
    if parts is None:
        raise ImportError("Module %r could not be found in system path"
                          % (path, ))
    return import_module_by_name_parts(*parts)


def import_child_modules(*parts):
    parent_module = import_module_by_name_parts(*parts)
    parent_dir = os.path.dirname(parent_module.__file__)
    modules = {}
    for child in os.listdir(parent_dir):
        if child.startswith("_"):
            continue
        child_name = fin.string.rtrim(child, *PY_EXTENSIONS)
        if child_name == child:
            continue
        try:
            modules[child_name] = import_module_by_name_parts(
                *(tuple(parts) + (child_name, )))
        except ImportError:
            continue
    return modules


def get_fully_qualified_object(name):
    """name could be, for example:  some.module.ClassA.method_b
       and this method should return a reference to method_b
       even if some.module isn't imported"""
    parts = name.split(".")
    base_module = parts[0]
    path = parts[1:]
    __import__(base_module)
    current_object = sys.modules[parts[0]]
    partial_path = [base_module]
    for part in path:
        partial_path.append(part)
        try:
            current_object = getattr(current_object, part)
        except AttributeError:
            try:
                __import__(".".join(partial_path))
            except ImportError:
                raise AttributeError("%r does not contain %r" %
                                     (".".join(partial_path[:-1]), part))
            else:
                current_object = getattr(current_object, part)
    return current_object
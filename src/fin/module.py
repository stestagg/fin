import imp
import inspect
import os
import os.path
import re
import sys
import types

import fin.string
import fin.exception


PY_EXTENSIONS = [ext for ext, _, _ in imp.get_suffixes()]


class PathNotImportable(fin.exception.Exception, ImportError):
    pass


class NoSysPathFound(fin.exception.Exception, ImportError):
    pass


def dir_is_module(path):
    assert os.path.isdir(path), path
    if "." in os.path.basename(path):
        return False
    if os.path.dirname(path) == path:
        return False
    if not any([os.path.exists(os.path.join(path, "__init__%s" % ext))
                for ext in PY_EXTENSIONS]):
        return False
    return True


def path_to_module_parts(path, auto_add=False):
    path = os.path.abspath(path)
    if os.path.isdir(path) and not dir_is_module(path):
        raise PathNotImportable(path)
    sys_paths = set(os.path.abspath(path) for path in sys.path)
    module_path = fin.string.rtrim(path, *PY_EXTENSIONS)
    base_path = module_path
    while True:
        base_path = os.path.dirname(base_path)  # Get the parent directory
        if base_path in sys_paths:  # Can import from here?
            break
        if not dir_is_module(base_path):
            # If we go any further, then the import will fail
            # so: if auto_add, then add this path to sys.paths, and use that...
            if auto_add:
                sys.path.insert(0, base_path)
                break
            else:
                # ... Otherwise, bail out
                raise NoSysPathFound(path)

    relative_path = module_path[len(base_path):].strip(os.path.sep)
    filename = os.path.basename(relative_path)
    if fin.string.rtrim(filename, *PY_EXTENSIONS) == "__init__":
        relative_path = os.path.dirname(relative_path)
    return relative_path.split(os.path.sep)


def import_module_by_name_parts(*parts):
    __import__(".".join(parts))
    base = sys.modules[parts[0]]
    for part in parts[1:]:
        base = getattr(base, part)
    return base


def import_module_by_path(path, auto_add=False):
    parts = path_to_module_parts(path, auto_add=auto_add)
    return import_module_by_name_parts(*parts)


def import_child_modules(parts, ignore="^[\._].*", error_callback=None):
    matcher = None if ignore is None else re.compile(ignore)
    if isinstance(parts, types.ModuleType):
        parent_module = parts
        parts = path_to_module_parts(inspect.getfile(parts))
    else:
        parent_module = import_module_by_name_parts(*parts)
    parent_dir = os.path.dirname(inspect.getfile(parent_module))
    modules = {}
    for child in os.listdir(parent_dir):
        if matcher is not None and matcher.match(child):
            continue
        child_name = fin.string.rtrim(child, *PY_EXTENSIONS)
        child_path = os.path.join(parent_dir, child)
        if child_name == child and not os.path.isdir(child_path):
            continue
        if child_name in modules:
            continue
        try:
            modules[child_name] = import_module_by_name_parts(
                *(tuple(parts) + (child_name, )))
        except Exception, e:
            if error_callback is not None:
                error_callback(e)
            else:
                raise
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

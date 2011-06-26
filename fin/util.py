
import os
import sys

import fin.string


def filename_to_module_name(path):
    path = os.path.abspath(path)
    sys_paths = set(os.path.abspath(path) for path in sys.path)
    module_path = fin.string.rtrim(path, ".py", ".pyc", ".pyo")
    base_path = module_path
    while True:
        base_path = os.path.dirname(base_path)
        if base_path in sys_paths:
            break
        if os.path.dirname(base_path) == base_path:
            return None
    relative_path = (module_path[len(base_path):].strip(os.path.sep))
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


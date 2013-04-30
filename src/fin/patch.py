import contextlib


@contextlib.contextmanager
def patch(parent, name, object):
    old_object = getattr(parent, name)
    setattr(parent, name, object)
    try:
        yield
    finally:
        setattr(parent, name, old_object)
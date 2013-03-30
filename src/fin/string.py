

def substring(data, offset=None, size=None):
    """This function matches the buffer() behaviour, for certain applications
    it may be beneficial to assign fin.string.substring to buffer"""
    if offset is None and size is None:
        return data
    if size is None:
        return data[offset:]
    if offset is None:
        return data[:size]
    return data[offset:offset+size]


def ltrim(data, *prefixes):
    """If data begins with any of prefixes, returns a buffer pointing to
    the contents of data with the first matching prefix removed,
    otherwise returns data"""
    for prefix in prefixes:
        if data.startswith(prefix):
            return substring(data, len(prefix))
    return data


def rtrim(data, *suffixes):
    """If data ends with any of suffixes, returns a buffer pointing to
    the contents of data with the first matching suffix removed,
    otherwise returns data"""
    for suffix in suffixes:
        if data.endswith(suffix):
            return substring(data, 0, len(data) - len(suffix))
    return data


class _String(basestring):

    ltrim = ltrim
    rtrim = rtrim


class Str(_String, str):
    pass


class Unicode(_String, unicode):
    pass


def String(data):
    if isinstance(data, unicode):
        return Unicode(data)
    else:
        return Str(data)

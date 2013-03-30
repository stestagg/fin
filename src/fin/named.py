
import collections
import sys


if hasattr(collections, "namedtuple"):
    _namedtuple = collections.namedtuple
    def namedtuple(typename, *field_names):
        result = collections.namedtuple(typename, field_names)
        # For pickling to work, the __module__ variable needs to be set to 
        # the frame where the named tuple is created.  
        # Bypass this step in enviroments where sys._getframe is not defined 
        # (Jython for example) or sys._getframe is not defined for arguments
        # greater than 0 (IronPython).
        try:
            result.__module__ = sys._getframe(1).f_globals.get(
                "__name__", "__main__")
        except (AttributeError, ValueError):
            pass
        return result
else:
    import operator
    # Shamelessly copied from http://code.activestate.com/recipes/500261/
    def namedtuple(typename, *field_names):
        field_names = tuple(field_names)
        # Create and fill-in the class template
        numfields = len(field_names)
        # tuple repr without parens or quotes
        argtxt = repr(field_names).replace("'", "")[1:-1]
        reprtxt = ', '.join('%s=%%r' % name for name in field_names)
        template = '''class %(typename)s(tuple):
        '%(typename)s(%(argtxt)s)' \n
        __slots__ = () \n
        _fields = %(field_names)r \n
        def __new__(_cls, %(argtxt)s):
            return _tuple.__new__(_cls, (%(argtxt)s)) \n
        @classmethod
        def _make(cls, iterable, new=tuple.__new__, len=len):
            'Make a new %(typename)s object from a sequence or iterable'
            result = new(cls, iterable)
            if len(result) != %(numfields)d:
                raise TypeError('Expected %(numfields)d arguments, got %%d' %% len(result))
            return result \n
        def __repr__(self):
            return '%(typename)s(%(reprtxt)s)' %% self \n
        def _asdict(self):
            'Return a new dict which maps field names to their values'
            return dict(zip(self._fields, self)) \n
        def _replace(_self, **kwds):
            'Return a new %(typename)s object replacing specified fields with new values'
            result = _self._make(map(kwds.pop, %(field_names)r, _self))
            if kwds:
                raise ValueError('Got unexpected field names: %%r' %% kwds.keys())
            return result \n
        def __getnewargs__(self):
            return tuple(self) \n\n''' % locals()
        for i, name in enumerate(field_names):
            template += '        %s = _property(_itemgetter(%d))\n' % (name, i)
        namespace = dict(_itemgetter=operator.itemgetter, 
                         __name__='namedtuple_%s' % typename,
                         _property=property, 
                         _sys=sys,
                         _tuple=tuple)
        try:
            exec template in namespace
        except SyntaxError, e:
            raise
            raise SyntaxError(e.message + ':\n' + template)
        result = namespace[typename]

        # For pickling to work, the __module__ variable needs to be set to 
        # the frame where the named tuple is created.  
        # Bypass this step in enviroments where sys._getframe is not defined 
        # (Jython for example) or sys._getframe is not defined for arguments
        # greater than 0 (IronPython).
        try:
            result.__module__ = sys._getframe(1).f_globals.get(
                "__name__", "__main__")
        except (AttributeError, ValueError):
            pass
        return result

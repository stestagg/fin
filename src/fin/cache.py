
import functools
import copy
import contextlib

# Class objects do not like having their __dict__ members
# twiddled directly, so we have to use strings here
CACHE_KEY = "__FIN_CACHE"
PROPERTY_OVERRIDE_KEY = "__PROPERTY_CACHE"
DEPENDENCIES = object()


def _hasattr(obj, key):
    return key in obj.__dict__


class ResultCache(object):

    """
    Used internally to store and manage the cached results
    """

    def __init__(self, fun):
        self._fun = fun

    def get_cache(self, obj):
        if not _hasattr(obj, CACHE_KEY):
            setattr(obj, CACHE_KEY, {})
        cache = getattr(obj, CACHE_KEY)
        if self._fun not in cache:
            cache[self._fun] = ({}, [])
        return cache[self._fun]

    def reset(self, obj):
        if self.has_cached(obj):
            del getattr(obj, CACHE_KEY)[self._fun]

    @contextlib.contextmanager
    def temporary_cache(self, obj):
        old_cache = self.get_cache(obj)
        try:
            getattr(obj, CACHE_KEY)[self._fun] = ({}, [])
            yield
        finally:
            getattr(obj, CACHE_KEY)[self._fun] = old_cache

    def has_cached(self, obj):
        return _hasattr(obj, CACHE_KEY) and self._fun in getattr(obj, CACHE_KEY)

    def _run(self, obj, args, kwargs):
        return self._fun(obj, *args, **kwargs)

    def _get_result(self, obj, args, kwargs):
        dict_cache, list_cache = self.get_cache(obj)
        arg_key = (self.get_dependencies(obj), args, tuple(kwargs.items()))
        try:
            hash(arg_key)
            hashable = True
        except TypeError:
            hashable = False
        if hashable and arg_key in dict_cache:
            return dict_cache[arg_key]
        elif not hashable:
            for cached_key, result in list_cache:
                if cached_key == arg_key:
                    return result
        result = self._run(obj, args, kwargs)
        if hashable:
            dict_cache[arg_key] = result
        else:
            list_cache.append((copy.deepcopy(arg_key), result))
        return result

    def get_result(self, obj, args, kwargs):
        return self._get_result(obj, args, kwargs)

    def get_dependencies(self, obj):
        dependencies = self._fun.__dict__.get(DEPENDENCIES)
        if dependencies is None:
            return None
        return tuple(getattr(obj, dep) for dep in dependencies)


class GeneratorCache(ResultCache):

    def _run(self, obj, args, kwargs):
        return DynamicTee(self._fun(obj, *args, **kwargs))

    def get_result(self, obj, args, kwargs):
        return self._get_result(obj, args, kwargs).get_copy()


class DynamicTee(object):

    """
    Wraps a generator, and keeps a reference to all generated values.  calling get_copy() on a DynamicTee object creates an iterator
    that behaves as it it were a it were a fresh iterator over the same values.

    Example::
    
        >> i = iter([1,2,3,4])
        >> zip(i, i)
        [(1, 2), (3, 4)]
        >> j = DynamicTee(iter([1,2,3,4]))
        >> zip(j, j.get_copy())
        [(1, 1), (2, 2), (3, 3), (4, 4)]
    """

    class TeeGenerator(object):

        def __init__(self, dynamic_tee):
            self.tee = dynamic_tee
            self.index = 0

        def __next__(self):
            val = self.tee[self.index]
            self.index += 1
            return val

        next = __next__

        def __iter__(self):
            return self

    def __init__(self, generator):
        self._stopped = False
        if not hasattr(generator, "__next__"):
            self._generator = iter(generator)
        else:
            self._generator = generator
        self._generated = []
        
    def get_copy(self):
        return self.TeeGenerator(self)

    def __getitem__(self, index):
        if index == len(self._generated):
            self._generated.append(next(self._generator))
        return self._generated[index]


def depends(*attributes):
    """
    Used in conjunction with :func:`fin.cache.property` or :func:`fin.cache.method`, this decorator tags a cached method as depending
    on the value of the specified named attribute on the method's object.  Note, this does mean all dependant properties are evaluated
    every time the cached method is called.

    As a naive example, to cache an object hash, where the hashing algorithm might change::

        >>> class HashedValue(object):
        
        >>>    def __init__(self, value):
        >>>        self.value = value
        >>>        self.hash_method = "sha1"

        >>>    @fin.cache.property
        >>>    @fin.cache.depends("value", "hash_method")
        >>>    def hash(self):
        >>>        print('** Calculating **')
        >>>        return getattr(hashlib, self.hash_method)(self.value).hexdigest()

        >>> val = HashedValue('hello')
        >>> val.hash
        ** Calculating **
        'aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d'
        >>> val.hash
        'aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d'
        >>> val.hash_method = 'sha1'
        >>> val.hash
        'aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d'
        >>> val.hash_method = 'sha512'
        >>> val.hash
        ** Calculating **
        '9b71d224bd62f3785d96d46ad3ea3d73319bfbc2890caadae2dff72519673ca72323c3d99ba5c11d7c7acc6e14b8c5da0c4663475c2e5c3adef46f73bcdec043'

    In this case, ``instance.hash`` will always reflect the currently selected hashing method, and the current value, but will not re-hash the 
    value needlessly.
    """
    def mutate(fun):
        fun.__dict__[DEPENDENCIES] = attributes
        return fun
    return mutate


def _wrap_fun_with_cache(fun, cache_type):
    cache = cache_type(fun)

    @functools.wraps(fun)
    def wrapper(obj, *args, **kwargs):
        return cache.get_result(obj, args, kwargs)

    for method_name in ['reset', 'has_cached', 'temporary_cache']:
        bound_method = getattr(cache, method_name, None)
        if bound_method is not None:
            setattr(wrapper, method_name, bound_method)
    return wrapper


def method(fun):
    """
    This is the core of ``fin.cache``.  Typically used as a decorator on class or instance methods.  
    When a method is decorated with this function, repeatedly calling it, on the same object, 
    with the same arguments*, will only cause the method to be called once.
    The result of that call is stored on the object, and is automatically returned subsequently. 

    An interesting (contrived) example from the tests::

        class Factorial(object):

            #Try commenting out the @fin.cache.method line and see what happens..
            @fin.cache.method
            def factorial(self, num):
                if num <= 1:
                    return 1
                return num * self.factorial(num - 1)

        factorial = Factorial()
        for i in range(2000):
            factorial.factorial(i)

    \* **NOTE**: Arguments are tested by equality (``a==b`` not ``a is b``).  This can, in a very few situations, lead to unexpected results.
      Also, the result value is cached by reference.  If a cached method returns, for example, a ``list``, then any modifications to that list will 
      be shared amongst all return values, which can lead to some strange effects if mis-used::

        >>> class Bad(object):

        >>>     @classmethod
        >>>     @fin.cache.method
        >>>     def bad_range(self, n):
        >>>         return list(range(n))

        >>> nums = Bad.bad_range(1)
        >>> print(Bad.bad_range(1), Bad.bad_range(2))
        [0] [0, 1]
        >>> nums.extend(Bad.bad_range(2))
        >>> print(Bad.bad_range(1), Bad.bad_range(2))
        [0, 0, 1] [0, 1]

    Calling ``reset(object)`` on the descriptor will cause the cache to be cleared for that object, to continue the example::

        >>> Bad.bad_range.reset(Bad)
        >>> print(Bad.bad_range(1), Bad.bad_range(2))
        [0] [0, 1]

    When used on an instance method, rather than a classmethod, the object instance should be passed into reset.
    """
    return _wrap_fun_with_cache(fun, ResultCache)

_classmethod = classmethod

def classmethod(fun):
    return _classmethod(_wrap_fun_with_cache(fun, ResultCache))


def generator(fun):
    """
    **Use with care!** This generator keeps a reference to all generated values for the lifetime of the cache (unless manually cleared).
    Given that generators are often used to handle larger volumes of data, this may cause memory issues if used incorrectly.  This decorator
    is useful as a speed optimisation, but comes with a memory cost.

    Acts like ``@fin.cache.method`` but for methods that return a generator (or uses :keyword:yield).  Repeated calls to this method return an
    object that can be used to iterate over the generated values from the start::

        >>> class Example(object):
        >>> 
        >>>     @fin.cache.generator
        >>>     def slow_range(self, num):
        >>>         for i in range(num):
        >>>             time.sleep(0.2)
        >>>             yield i

        >>> e = Example()
        >>> e.slow_range(10)
        <fin.cache.TeeGenerator at 0x7f9041062650> # Fast
        >>> list(e.slow_range(10))
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]             # Slow
        >>> list(e.slow_range(10))
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]             # Fast (already calculated)
        >>> list(e.slow_range(5))
        [0, 1, 2, 3, 4]                            # Slow (different arguments used)
        >>> list(Example().slow_range(10))
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]             # Slow (different instance used)
        >>> Example.slow_range.reset(e) # Free the memory..
        >>> list(e.slow_range(10))
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]             # Slow (cache has been cleared)

    The generator is evaluated on-demand, and lazily, so the following works:

        >>> timeit(lambda: list(e.slow_range(3)), number=1)
        # Takes 0.6 seconds to evaluate the list
        0.60060    #  [0, 1, 2]
        >>> e.slow_range.reset(e)
        >>> timeit(lambda: zip(e.slow_range(10), e.slow_range(10)))  
        # Both generators are being evaluated at the same time, but the time stays the same:
        0.60075   #  [(0, 0), (1, 1), (2, 2)]

    """
    return _wrap_fun_with_cache(fun, GeneratorCache)


class property(object):
    """
    This decorator behaves like the builtin :keyword:`@property` decorator, but caches the results, similarly to ``fin.cache.method``::

        >>> class Example(object):

        >>>     @fin.cache.property
        >>>     def number(self):
        >>>         time.sleep(1)
        >>>         return 4

        >>> e = Example()
        >>> print "Slow:", e.number
        Slow: 4  (1 second later)
        >>> print "Fast:", e.number
        Fast: 4  (immediately)
        >>> E.number.reset(e)
        >>> print "Slow:", e.number
        Slow: 4  (1 second later)

    :func:`@fin.cache.property` descriptors support assignment.  The attribute can be assigned a callable, 
    taking one argument, which will always be called on attribute access, and the result returned.  
    This is best shown by an example, continuing from the previous::

        >>> e = Example()
        >>> f = Example()
        >>> print(e.number, f.number)
        4 4
        >>> f.number = lambda e: 8
        >>> print(e.number, f.number, f.number)
        4 8 8
        >>> e.number = lambda e: random.randint(1, 10)
        >>> print(e.number, f.number, f.number)
        4 5 9

    """

    def __init__(self, fun, wrapper=method):
        self._method = wrapper(fun)
        self.__doc__ = getattr(fun, "__doc__", None)
        self.temporary_cache = self._method.temporary_cache

    def __get__(self, inst, cls):
        if inst is None:
            return self
        if (_hasattr(inst, PROPERTY_OVERRIDE_KEY)
                and self in getattr(inst, PROPERTY_OVERRIDE_KEY)):
            return getattr(inst, PROPERTY_OVERRIDE_KEY)[self](inst)
        else:
            return self._method(inst)

    def __set__(self, inst, obj):
        if obj is None:
            return self._method.reset(inst)
        assert callable(obj)
        if not _hasattr(inst, PROPERTY_OVERRIDE_KEY):
            setattr(inst, PROPERTY_OVERRIDE_KEY, {})
        getattr(inst, PROPERTY_OVERRIDE_KEY)[self] = obj

    def reset(self, inst):
        """
        'Forgets' any cached value for instance ``inst``.  Use as shown in in the example above.  
        """
        self._method.reset(inst)

    def has_cached(self, inst):
        """
        Returns :keyword:`True` if a result has been  cached for the property on the specified instance:

            >>> class Example(object):
            >>>
            >>>     @fin.cache.property
            >>>     def one(self):
            >>>         return 1

            >>> e = Example()
            >>> Example.one.has_cached(e)
            False
            >>> e.one
            1
            >>> Example.one.has_cached(e)
            True
            >>> Example.one.reset(e)
            >>> Example.one.has_cached(e)
            False
        """
        return self._method.has_cached(inst)


def uncached_property(fun):
    """
    Behaves like the builtin :keyword:`@property` decorator, but supports the same assignment logic as ``@fin.cache.property``.  
    This method performs **no** caching, but is syntactic sugar.
    """
    return property(fun, wrapper=lambda x: x)
    

def invalidates(other):
    """
    Explicitly clears another cached method when this method is called, on the same object:

        >>> class Dice(object):
        >>>     @fin.cache.property
        >>>     def current_value(self):
        >>>         return random.randint(1, 7)
        >>>
        >>>     @fin.cache.invalidates(current_value)
        >>>     def roll(self):
        >>>         print("Rolling...")

        >>> die = Dice()
        >>> die.current_value
        1
        >>> die.current_value
        1
        >>> die.roll()
        >>> die.current_value
        5


    """
    def wrap(fun):
        @functools.wraps(fun)
        def invalidate_then_call(ob, *args, **kwargs):
            other.reset(ob)
            return fun(ob, *args, **kwargs)
        return invalidate_then_call
    return wrap

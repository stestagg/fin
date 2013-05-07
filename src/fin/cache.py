
import functools
import copy

# Class objects do not like having their __dict__ members
# twiddled directly, so we have to use strings here
CACHE_KEY = "__FIN_CACHE"
PROPERTY_OVERRIDE_KEY = "__PROPERTY_CACHE"
DEPENDANCIES = object()


class ResultCache(object):

    def __init__(self, fun):
        self._fun = fun

    def get_cache(self, obj):
        if not hasattr(obj, CACHE_KEY):
            setattr(obj, CACHE_KEY, {})
        cache = getattr(obj, CACHE_KEY)
        if self._fun not in cache:
            cache[self._fun] = ({}, [])
        return cache[self._fun]

    def reset(self, obj):
        if self.has_cached(obj):
            del getattr(obj, CACHE_KEY)[self._fun]

    def has_cached(self, obj):
        return hasattr(obj, CACHE_KEY) and self._fun in getattr(obj, CACHE_KEY)

    def _run(self, obj, args, kwargs):
        return self._fun(obj, *args, **kwargs)

    def _get_result(self, obj, args, kwargs):
        dict_cache, list_cache = self.get_cache(obj)
        arg_key = (self.get_dependancies(obj), args, tuple(kwargs.items()))
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

    def get_dependancies(self, obj):
        dependancies = self._fun.__dict__.get(DEPENDANCIES)
        if dependancies is None:
            return None
        return tuple(getattr(obj, dep) for dep in dependancies)


class GeneratorCache(ResultCache):

    def _run(self, obj, args, kwargs):
        return DynamicTee(self._fun(obj, *args, **kwargs))

    def get_result(self, obj, args, kwargs):
        return self._get_result(obj, args, kwargs).get_copy()


class DynamicTee(object):

    class TeeGenerator(object):

        def __init__(self, dynamic_tee):
            self.tee = dynamic_tee
            self.index = 0

        def next(self):
            val = self.tee[self.index]
            self.index += 1
            return val

        def __iter__(self):
            return self

    def __init__(self, generator):
        self._stopped = False
        if not hasattr(generator, "next"):
            self._generator = iter(generator)
        else:
            self._generator = generator
        self._generated = []
        
    def get_copy(self):
        return self.TeeGenerator(self)

    def __getitem__(self, index):
        if index == len(self._generated):
            self._generated.append(self._generator.next())
        return self._generated[index]


def depends(*attributes):
    def mutate(fun):
        fun.__dict__[DEPENDANCIES] = attributes
        return fun
    return mutate


def _wrap_fun_with_cache(fun, cache_type):
    cache = cache_type(fun)

    @functools.wraps(fun)
    def wrapper(obj, *args, **kwargs):
        return cache.get_result(obj, args, kwargs)
    wrapper.reset = cache.reset
    wrapper.has_cached = cache.has_cached
    return wrapper


def method(fun):
    return _wrap_fun_with_cache(fun, ResultCache)


def generator(fun):
    return _wrap_fun_with_cache(fun, GeneratorCache)


class property(object):

    def __init__(self, fun, wrapper=method):
        self._method = wrapper(fun)
        self.__doc__ = getattr(fun, "__doc__", None)

    def __get__(self, inst, cls):
        if inst is None:
            return self
        if (hasattr(inst, PROPERTY_OVERRIDE_KEY)
                and self in getattr(inst, PROPERTY_OVERRIDE_KEY)):
            return getattr(inst, PROPERTY_OVERRIDE_KEY)[self](inst)
        else:
            return self._method(inst)

    def __set__(self, inst, obj):
        if obj is None:
            return self._method.reset(inst)
        assert callable(obj)
        if not hasattr(inst, PROPERTY_OVERRIDE_KEY):
            setattr(inst, PROPERTY_OVERRIDE_KEY, {})
        getattr(inst, PROPERTY_OVERRIDE_KEY)[self] = obj

    def reset(self, inst):
        self._method.reset(inst)

    def has_cached(self, inst):
        return self._method.has_cached(inst)


def uncached_property(fun):
    return property(fun, wrapper=lambda x: x)
    

def invalidates(other):
    def wrap(fun):
        @functools.wraps(fun)
        def invalidate_then_call(ob, *args, **kwargs):
            other.reset(ob)
            return fun(ob, *args, **kwargs)
        return invalidate_then_call
    return wrap

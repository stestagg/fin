import functools


class DuplexMethod(object):

	def __init__(self, func, class_method=None, inst_lookup_fun=None):
		self.func = func
		self.class_method = class_method
		self.inst_lookup_fun = inst_lookup_fun

	def make_wrapper(self, finder, *args, **kwargs):
		@functools.wraps(self.func)
		def runner(*args, **kwargs):
			obj = finder()
			return self.func(obj, *args, **kwargs)

	def __get__(self, obj, cls=None):
		if obj is None:
			if self.class_method is not None:
					return self.class_method.__get__(cls, cls)

			@functools.wraps(self.func)
			def run_wrapped(*args, **kwargs):
				if self.inst_lookup_fun is not None:
					obj = self.inst_lookup_fun(cls)
				else:
					obj = cls
				return self.func.__get__(obj, cls)(*args, **kwargs)
			return run_wrapped
		return self.func.__get__(obj, cls)

	def classmethod(self, func):
		self.class_method = func
		return self


def method(*args, **kwargs):
	"""
	Create a duplex method.  Duplex methods can be called as an instance OR a classmethod using the same
	function name.  Usage is similar to @classmethod, but the first (self) argument to the function, when called,
	will be bound to either an instance OR a class object depending on how it is called.

	Example:

	class A(object):
		@fin.dumplex.method
		def me(obj):
			return obj

	>>>  A.me() == <class 'A'>
	>>>  A().me() == <A object at 0x1006cf350>

	"""

	if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
		func, = args
		return DuplexMethod(func)
	def wrapper(func):
		return DuplexMethod(func, *args, **kwargs)
	return wrapper
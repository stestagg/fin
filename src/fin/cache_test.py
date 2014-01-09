
import collections
import itertools

import fin.testing
import fin.cache


class SimpleTests(fin.testing.TestCase):

    def test_property(self):
        class Counter(object):
            def __init__(self):
                self.counter = itertools.count()

            @property
            def count(self):
                return self.counter.next()

            @fin.cache.property
            def dont_count(self):
                return self.counter.next()

        cache = Counter()
        for i in range(10):
            self.assertEqual(cache.dont_count, 0)
            self.assertEqual(cache.count, i+1)

    def test_overwriting_property(self):
        class Counter(object):
            def __init__(self):
                self.counter = itertools.count()

            @fin.cache.property
            def count(self):
                return self.counter.next()

        cache1 = Counter()
        cache2 = Counter()
        cache1.count = lambda x: "a"
        cache2.count = lambda x: "b"
        self.assertEqual(cache1.count, "a")
        self.assertEqual(cache2.count, "b")

    def test_mutable_args(self):
        class Counter(object):
            def __init__(self):
                self.counter = itertools.count()

            @fin.cache.method
            def count(self, data):
                return self.counter.next()

        cache = Counter()
        a = {"b": {"c": []}}
        self.assertEqual(cache.count(a), 0)
        self.assertEqual(cache.count(a), 0)
        a["b"]["c"].append(1)
        self.assertEqual(cache.count(a), 1)

    def test_doc_inheritance(self):
        class Foo(object):

            @fin.cache.method
            def meth(self, data):
                "a method"
                pass

            @fin.cache.property
            def prop(self):
                "a property"
                pass

        self.assertEqual(Foo.meth.__doc__, "a method")
        self.assertEqual(Foo().meth.__doc__, "a method")
        self.assertEqual(Foo.prop.__doc__, "a property")

    def test_getting_classattr(self):
        class Counter(object):
            def __init__(self):
                self.counter = itertools.count()

            @fin.cache.property
            def count(self, data):
                return self.counter.next()

        ob = Counter.count
        assert isinstance(ob, fin.cache.property)

    def test_resetting(self):
        class Counter(object):
            def __init__(self):
                self.counter = itertools.count()

            @fin.cache.method
            def do_count(self):
                return self.counter.next()

            @fin.cache.property
            def count(self):
                return self.counter.next()

        cache = Counter()
        self.assertEqual(cache.count, 0)
        self.assertEqual(cache.count, 0)
        self.assertEqual(cache.do_count(), 1)
        self.assertEqual(cache.do_count(), 1)
        cache.count = None
        self.assertEqual(cache.count, 2)
        self.assertEqual(cache.count, 2)
        cache.do_count.reset(cache)
        self.assertEqual(cache.do_count(), 3)
        self.assertEqual(cache.do_count(), 3)
        Counter.count.reset(cache)
        self.assertEqual(cache.count, 4)

    def test_depends(self):
        class Counter(object):
            def __init__(self):
                self.count = 0

            @property
            def div5(self):
                return self.count/5

            @fin.cache.property
            @fin.cache.depends("div5")
            def slow_counter(self):
                return self.count

        cache = Counter()
        for i in range(20):
            cache.count = i
            self.assertEqual(cache.slow_counter, (i/5)*5)

    def test_non_hashable(self):
        class Counter(object):
            def __init__(self):
                self.counter = itertools.count()

            @fin.cache.method
            def append(self, l):
                return l + [self.counter.next()]

        cache = Counter()
        self.assertEqual(cache.append([1, 2]), [1, 2, 0])
        self.assertEqual(cache.append([1, 3]), [1, 3, 1])
        self.assertEqual(cache.append([1, 3]), [1, 3, 1])
        self.assertEqual(cache.append([1, 2]), [1, 2, 0])
        self.assertEqual(cache.append([1, 2, 3]), [1, 2, 3, 2])

    def test_has_cached(self):
        class Ob(object):

            @fin.cache.method
            def method(self, l):
                return l

            @fin.cache.property
            def prop(self):
                return True

        cache = Ob()
        self.assertFalse(cache.method.has_cached(cache))
        self.assertFalse(Ob.prop.has_cached(cache))
        self.assertFalse(cache.method.has_cached(cache))
        self.assertFalse(Ob.prop.has_cached(cache))
        cache.method(1)
        self.assertTrue(cache.method.has_cached(cache))
        self.assertFalse(Ob.prop.has_cached(cache))
        cache.method.reset(cache)
        cache.prop
        self.assertFalse(cache.method.has_cached(cache))
        self.assertTrue(Ob.prop.has_cached(cache))
        cache.method(2)
        self.assertTrue(cache.method.has_cached(cache))
        self.assertTrue(Ob.prop.has_cached(cache))


class GeneratorTest(fin.testing.TestCase):

    def test_generator(self):
        class SsItertools(object):
            @fin.cache.generator
            def count(self):
                return itertools.count()
        ssitertools = SsItertools()
        a = ssitertools.count()
        b = ssitertools.count()
        self.assertEqual(a.next(), 0)
        self.assertEqual(b.next(), 0)

    def test_yield(self):
        counter = itertools.count()

        class SsItertools(object):
            @property
            @fin.cache.generator
            def count(self):
                for i in range(10):
                    yield i
                    counter.next()

        ssitertools = SsItertools()
        cached1 = ssitertools.count
        cached2 = ssitertools.count
        self.assertEqual(counter.next(), 0)
        for i, j in enumerate(cached1):
            self.assertEqual(i, j)
            self.assertEqual(cached2.next(), j)
        self.assertEqual(counter.next(), 11)

    def test_arguments(self):

        class Apples(object):

            def __init__(self, apples):
                self.apples = apples

            @fin.cache.generator
            def gimmeh(self, num):
                for i in range(num):
                    self.apples -= 1
                    yield 1

        apples = Apples(10)
        basket = apples.gimmeh(5)
        self.assertEqual(apples.apples, 10)
        self.assertEqual(sum(apple for apple in basket), 5)
        self.assertEqual(apples.apples, 5)
        self.assertRaises(StopIteration, basket.next)
        magic_basket = apples.gimmeh(5)
        self.assertEqual(apples.apples, 5)
        for apple in magic_basket:
            self.assertRaises(StopIteration, basket.next)
        self.assertEqual(apples.apples, 5)
        self.assertRaises(StopIteration, magic_basket.next)
        small_basket = apples.gimmeh(4)
        self.assertEqual(apples.apples, 5)
        self.assertEqual(sum(apple for apple in small_basket), 4)
        self.assertEqual(apples.apples, 1)
        self.assertRaises(StopIteration, small_basket.next)


class ExampleCache(object):

    def __init__(self, callback):
        self.callback = callback
        self.epoch = 1

    @classmethod
    @fin.cache.method
    def antimony(cls, callback):
        callback("antimony")
        return cls(callback)

    @fin.cache.method
    def arsenic(self):
        self.callback("arsenic")
        return "Element"

    @fin.cache.method
    def selenium(self, *args, **kwargs):
        self.callback("selenium")
        return args[0]

    @fin.cache.property
    def aluminium(self):
        self.callback("aluminium")
        return "stuff"

    @fin.cache.property
    @fin.cache.depends("epoch")
    def hydrogen(self):
        self.callback("hydrogen")
        return "H" + str(self.epoch)

    @fin.cache.property
    @fin.cache.depends("hydrogen")
    def oxygen(self):
        self.callback("oxygen")
        return "O"


class CacheTest(fin.testing.TestCase):

    def setUp(self):
        self.counters = collections.defaultdict(int)
        self.counter = 0

    def _count(self, func):
        self.counters[func] += 1

    def _simple_count(self, func):
        self.counter += 1

    def test_once(self):
        a = ExampleCache.antimony(self._count)
        b = ExampleCache.antimony(self._count)
        self.assertTrue(a is b)
        self.assertEqual(self.counters["antimony"], 1)
        self.assertEqual(a.arsenic(), "Element")
        self.assertEqual(self.counters["arsenic"], 1)
        self.assertEqual(a.arsenic(), "Element")
        self.assertEqual(self.counters["arsenic"], 1)
        self.assertEqual(a.aluminium + b.aluminium, "stuffstuff")
        self.assertEqual(self.counters["aluminium"], 1)
        for i in [1, 1, 2, 3, 5]:
            self.assertEqual(b.selenium(i), i)
        self.assertEqual(self.counters["selenium"], 4)
        for i in [[1, 2], [1], [34], ("a", "b")]:
            self.assertEqual(b.selenium(i), i)
        self.assertEqual(self.counters["selenium"], 8)

    def test_depends(self):
        a = ExampleCache(self._simple_count)
        self.assertEqual(a.hydrogen + a.oxygen, "H1O")
        self.assertEqual(a.hydrogen + a.oxygen, "H1O")
        self.assertEqual(self.counter, 2)
        a.epoch = 2
        self.assertEqual(a.hydrogen + a.oxygen, "H2O")
        self.assertEqual(a.hydrogen + a.oxygen, "H2O")
        self.assertEqual(self.counter, 4)
        a.epoch = 1
        self.assertEqual(a.hydrogen + a.oxygen, "H1O")
        self.assertEqual(a.hydrogen + a.oxygen, "H1O")
        self.assertEqual(self.counter, 4)

    def test_overwriting(self):
        counter = itertools.count()
        
        def count(inst):
            return counter.next()
        a = ExampleCache(self._simple_count)
        a.hydrogen = fin.cache.method(fin.cache.depends("epoch")(count))
        self.assertEqual(a.hydrogen, 0)
        self.assertEqual(a.hydrogen, 0)
        a.epoch = 2
        self.assertEqual(a.hydrogen, 1)
        self.assertEqual(a.hydrogen, 1)


class FactorialTest(fin.testing.TestCase):

    #Try disabling the cache decorator to see what happens
    @fin.cache.method
    def factorial(self, num):
        if num <= 1:
            return 1
        return num * self.factorial(num - 1)

    def test_factorial(self):
        for i in range(2000):
            self.factorial(i)


class TestInvalidation(fin.testing.TestCase):

    def test_invalidating(self):
        counter = itertools.count()

        class Foo(object):

            @fin.cache.property
            def a_number(self):
                return counter.next()

            @fin.cache.invalidates(a_number)
            def next(self):
                pass

        ob = Foo()
        self.assertEqual(ob.a_number, 0)
        self.assertEqual(ob.a_number, 0)
        ob.next()
        self.assertEqual(ob.a_number, 1)
        self.assertEqual(ob.a_number, 1)


class TestCacheSharing(fin.testing.TestCase):

    def test_sharing_caches(self):
        counter = itertools.count()
        class Foo(object):
            @classmethod
            @fin.cache.method
            def foo(cls):
                return counter.next()

            @fin.cache.method
            def bar(self):
                return counter.next()

        first = Foo.foo()
        inst = Foo()
        second = inst.bar()
        third = Foo().bar()
        fourth = inst.bar()
        self.assertEqual(first, 0)
        self.assertEqual(second, 1)
        self.assertEqual(third, 2)
        self.assertEqual(fourth, 1)

    def test_subclasses_are_independant(self):
        class A(object):
            VAL = 1
            @classmethod
            @fin.cache.method
            def foo(cls):
                return cls.VAL

        class B(A):
            VAL = 2

        self.assertEqual(A.foo(), 1)
        self.assertEqual(B.foo(), 2)


if __name__ == "__main__":
    fin.testing.main()

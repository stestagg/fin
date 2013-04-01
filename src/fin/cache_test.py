
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


if __name__ == "__main__":
    fin.testing.main()

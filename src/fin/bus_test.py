# (C) Steve Stagg, 2011

import unittest2
import Queue
import multiprocessing

import fin.bus


class QueueHandler(fin.bus.Handler):

    def __init__(self, queue):
        self.queue = queue


class Stage1Handler(QueueHandler):

    def test(self, bus):
        self.queue.put("Foo")

    def pass_on(self, bus, data):
        bus.stage2(data + ".1")


class Stage2Handler(QueueHandler):

    def stage2(self, bus, data):
        self.queue.put(data + ".2")


class TestBus(fin.bus.Bus):

    MESSAGE_TYPES = ("test", "pass_on", "stage2")

    def __init__(self, num, queue):
        handlers = [Stage1Handler(queue), Stage2Handler(queue)]
        super(TestBus, self).__init__(handlers, num)
        self.queue = queue


class BusTest(unittest2.TestCase):

    def _make_bus(self, num):
        if num == 0:
            results = Queue.Queue()
        else:
            results = multiprocessing.Queue()
        bus = TestBus(num, results)
        return bus

    def test_simple_call(self):
        for num in (0, 1, 2):
            bus = self._make_bus(num)
            try:
                bus.test()
                bus.join()
                self.assertEqual(bus.queue.get(), "Foo")
            finally:
                bus.close()

    def test_chained_call(self):
        for num in (0, 1, 2):
            bus = self._make_bus(num)
            try:
                bus.pass_on(str(num))
                bus.join()
                self.assertEqual(bus.queue.get(), "%i.1.2" % num)
            finally:
                bus.close()


if __name__ == "__main__":
    unittest2.main()

# (C) Steve Stagg

import functools
import multiprocessing
import time

import fin.named


class StopWorker(object): pass


BusMessage = fin.named.namedtuple("BusMessage", "name", "args", "kwargs")


class Bus(object):

    MESSAGE_TYPES = ()
    
    def __init__(self, handlers, num=0):
        self.num_jobs = num
        dispatch_factory = SynchronousDispatcher if num == 0 else MPDispatcher
        self.dispatchers = [
            dispatch_factory(self, handler) for handler in handlers]
        for dispatcher in self.dispatchers:
            # Without this two step approach, you get some odd 
            # synchronisation effects
            dispatcher.start()

    def join(self):
        for dispatcher in self.dispatchers:
            dispatcher.join()

    def close(self):
        for dispatcher in self.dispatchers:
            dispatcher.close()        
        
    def _describe_message(self, message):
        args = []
        for arg in message.args:
            args.append(repr(arg))
        for name, value in message.kwargs.iteritems():
            args.append("%s=%r" % (name, value))
        return "%s(%s)" % (message.name, ",".join(args))

    def _handle_message(self, name, *args, **kwargs):
        message = BusMessage(name, args, kwargs)
        for dispatcher in self.dispatchers:
            if dispatcher.handles_message(message):
                dispatcher.receive_message(message)
                return

    def __getattr__(self, name):
        if name not in self.MESSAGE_TYPES:
            raise AttributeError(name)
        return functools.partial(self._handle_message, name)


class Dispatcher(object):

    def __init__(self, bus, handler):
        super(Dispatcher, self).__init__()
        self.bus = bus
        self.handler = handler

    def start(self):
        pass

    def handles_message(self, message):
        name, args, kwargs = message
        return self.handler.async_handles_message(name, *args, **kwargs)
    
    def join(self):
        pass

    def close(self):
        pass


class SynchronousDispatcher(Dispatcher):

    def receive_message(self, message):
        name, args, kwargs = message
        self.handler.receive_message(self.bus, name, *args, **kwargs)


class MPDispatcher(Dispatcher):

    def __init__(self, bus, handler):
        super(MPDispatcher, self).__init__(bus, handler)
        self.input = multiprocessing.JoinableQueue()
        self.processes = []
        process_count = bus.num_jobs
        if handler.LIMIT is not None:
            process_count = min(handler.LIMIT, process_count)
        for i in range(process_count):
            process = multiprocessing.Process(target=self.run)
            self.processes.append(process)            

    def start(self):
        for process in self.processes:
            process.start()

    def receive_message(self, message):
        self.input.put(message)

    def run(self):
        while True:
            message = self.input.get()
            if isinstance(message, StopWorker):
                return
            name, args, kwargs = message
            try:
                getattr(self.handler, name)(self.bus, *args, **kwargs)
            finally:
                # Bug in multiprocessing where it falsely thinks
                # task_done has been over-called
                for i in xrange(10):
                    try:
                        self.input.task_done()
                        break
                    except ValueError:
                        time.sleep(0.01)
                else:
                    self.input.task_done()

    def join(self):
        self.input.join()

    def close(self):
        # This is quite a paranoid function
        self.join()
        while True:
            for i in range(len(self.processes)):
                self.input.put(StopWorker())
            for process in self.processes:
                process.join(0.1)
            self.processes = [process for process in self.processes 
                              if process.is_alive()]
            if len(self.processes) == 0:
                return


class Handler(object):

    LIMIT = None

    def async_handles_message(self, name, *args, **kwargs):
        return name in dir(self)

    def receive_message(self, bus, name, *args, **kwargs):
        getattr(self, name)(bus, *args, **kwargs)

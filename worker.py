# worker.py                                                                                                        

import sys
import tasklib
import threading

class UnavailableError(Exception): pass

class FutureResult:

    def __init__(self, callback=None):
        self._cb = None if not callback else callback()
        self._evt = threading.Event()
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def set(self,value):
        self._value = value
        self._evt.set()

        if self._cb:
            threading.Thread(target=self._cb.next, args=(value,))

    def set_error(self):
        self._exc = sys.exc_info()
        self._evt.set()

        if self._cb:
            threading.Thread(target=self._cb.throw, args=(self._exc[0],))

    def get(self):
        self._evt.wait()
        if hasattr(self,"_exc"):
            raise RuntimeError("Worker Exception") from self._exc[1]
        if hasattr(self,"_value"):
            return self._value
        else:
            raise UnavailableError("No result")


class WorkerTask(tasklib.Task):

    def apply(self,func,args=(),kwargs={}, callback=None):
        fresult = FutureResult(callback=callback)
        self.send((fresult,func,args,kwargs))
        return fresult

    def run(self):
        while True:
            fresult,func,args,kwargs = self.recv()
            if fresult._cancelled:
                fresult.set(None)
            try:
                fresult.set(func(*args,**kwargs))
            except:
                fresult.set_error()

class WorkerPool(tasklib.Task):

    class Stop:
        pass

    def __init__(self,nworkers=1):
        super(WorkerPool,self).__init__(name="workerpool")
        self.nworkers = nworkers

    def apply(self,func,args=(),kwargs={}):
        fresult = FutureResult()
        self.send((fresult,func,args,kwargs))
        return fresult

    def run(self):
        # Launch more worker threads
        for n in range(1,self.nworkers):
            thr = threading.Thread(target=self.do_work)
            thr.daemon = True
            thr.start()
        self.do_work()

    def stop(self):
        self.send((self.Stop,None,None,None))

    # Worker method (runs in multiple threads)
    def do_work(self):
        while True:
            fresult,func,args,kwargs = self.recv()
            if fresult is self.Stop:
                self.send((fresult,None,None,None)) # queue a Stop for the next thread
                self.log.info("Exit")
                return
            if fresult._cancelled:
                continue
            try:
                fresult.set(func(*args,**kwargs))
            except:
                fresult.set_error()

# tasklib.py

import threading
import logging
import time
import sys
import queue

class TaskStop(Exception): pass

class Task:
    def __init__(self,name="Task"):
        self.name = name
        self.state = "INIT"
        self.start_evt = threading.Event()
        self.stop_evt = threading.Event()
        self.queue = queue.Queue()

    # queue handling
    def send(self, msg):
        self.queue.put(msg)

    def recv(self):
        r = self.queue.get()
        if r is TaskStop:
            raise r
        return r

    # Task start
    def start(self):
        self.start_evt.clear()
        thr = threading.Thread(target=self.bootstrap)
        thr.daemon = True
        thr.start()
        self.start_evt.wait()

    # Task bootstrap
    def bootstrap(self):
        self.runnable = True
        self.log = logging.getLogger(self.name)
        self.exc_info = None
        self.state = "RUNNING"
        self.log.info("Task starting")
        self.start_evt.set()
        try:
            self.run()
        except TaskStop:
            pass
        except Exception:
            self.exc_info = sys.exc_info()
            self.log.error("Crashed", exc_info=True)
        self.stop_evt.set()
        self.log.info("Exit")
        self.state = "EXIT"

    # Task stop
    def stop(self, wait=False):
        self.runnable = False
        self.queue.put(TaskStop)
        if wait:
            self.stop_evt.wait()
        self.stop_evt.clear()

    # Task finalization
    def finalize(self):
        del self.log
        del self.exc_info
        del self.runnable
        self.state = "FINAL"

    # Debugging support
    def pm(self):
        import pdb
        if self.exc_info:
            pdb.post_mortem(self.exc_info[2])
        else:
            print("No traceback")

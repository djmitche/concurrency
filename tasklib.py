# tasklib.py

import threading
import logging
import sys
import queue

class TaskExit(Exception): pass
class RecvTimeoutError(Exception): pass

class Task:
    name_counter = 0
    def __init__(self,name="Task"):
        if '%' in name:
            self.name_counter += 1
            name = name.replace('%', str(self.name_counter))
        self.name = name
        self.state = "INIT"

    # Task start
    def start(self):
        register(self.name, self)
        start_evt = threading.Event()
        thr = threading.Thread(target=self.bootstrap,args=(start_evt,))
        thr.daemon = True
        thr.start()
        # Wait for the task to start
        start_evt.wait()

    # Task bootstrap
    def bootstrap(self,start_event=None):
        self._exit_evt = threading.Event()
        self.runnable = True
        self.log = logging.getLogger(self.name)
        self.exc_info = None
        if not hasattr(self,"_messages"):
            self._messages = queue.Queue()
            self.messages_received = 0
        self.state = "RUNNING"
        self.log.info("Task starting")
        if start_event:
            start_event.set()
        try:
            self.run()
        except TaskExit:
            pass
        except Exception:
            self.exc_info = sys.exc_info()
            self.log.error("Crashed", exc_info=True)
        self.log.info("Exit")
        self.state = "EXIT"
        self._exit_evt.set()

    # Task join
    def join(self):
        self._exit_evt.wait()

    # Task messaging
    def send(self, msg):
        self._messages.put(msg)

    def recv(self,*,timeout=None):
        try:
            msg = self._messages.get(timeout=timeout)
        except queue.Empty:
            raise RecvTimeoutError("No message")
        if msg is TaskExit:
            raise TaskExit()
        self.messages_received += 1
        return msg

    @property
    def messages_pending(self):
        return self._messages.qsize()

    # Task stop
    def stop(self):
        unregister(self.name)
        self.runnable = False
        self.send(TaskExit)

    # Task finalization
    def finalize(self):
        del self.log
        del self.exc_info
        del self.runnable
        del self._exit_evt
        del self._messages
        del self.messages_received
        self.state = "FINAL"

    # Debugging support
    def pm(self):
        import pdb
        if self.exc_info:
            pdb.post_mortem(self.exc_info[2])
        else:
            print("No traceback")

# task messaging
_registry = {}

def register(name, task):
    _registry[name] = task

def unregister(name):
    del _registry[name]

def lookup(name):
    return _registry.get(name)

def send(target_name,msg):
    target = lookup(target_name)
    if target:
        return target.send(msg)
    else:
        print("Warning: target %r not registered" % target_name)
        return False

# tasklib.py

import threading
import logging
import sys

class Task:
    def __init__(self,name="Task"):
        self.name = name
        self.state = "INIT"

    # Task start
    def start(self):
        thr = threading.Thread(target=self.bootstrap)
        thr.daemon = True
        thr.start()

    # Task bootstrap
    def bootstrap(self):
        self.runnable = True
        self.log = logging.getLogger(self.name)
        self.exc_info = None
        self.state = "RUNNING"
        self.log.info("Task starting")
        try:
            self.run()
        except Exception:
            self.exc_info = sys.exc_info()
            self.log.error("Crashed", exc_info=True)
        self.log.info("Exit")
        self.state = "EXIT"

    # Task stop
    def stop(self):
        self.runnable = False

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

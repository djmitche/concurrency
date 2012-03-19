# countdown.py

import sys
import threading
import time
import logging

class CountdownTask:
    def __init__(self,count):
        self.count = count
        self.state = "INIT"

    # Launch the task
    def start(self):
        thr = threading.Thread(target=self.bootstrap)
        thr.daemon = True
        thr.start()

    # Set up the task run-time environment
    def bootstrap(self):
        self.log = logging.getLogger("countdown")
        self.log.info("Starting")
        self.state = "RUNNING"
        self.runnable = True
        self.exc_info = None
        try:
            self.run()
        except Exception:
            self.exc_info = sys.exc_info()
            self.log.error("Crashed", exc_info=True)
        self.log.info("Exit")
        self.state = "EXIT"

    # Request task stop
    def stop(self):
        self.runnable = False

    # Run the work of the task
    def run(self):
        while self.runnable and self.count > 0:
            print("Counting down", self.count)
            self.count -=1
            time.sleep(5)

    # Clean up the run-time environment
    def finalize(self):
        del self.log
        del self.runnable
        del self.exc_info
        self.state = "FINAL"

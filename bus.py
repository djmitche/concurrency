import math
import time
from socket import *
from threading import Thread
import tasklib

STOPPED, RUNNING, STOPPING = range(3)

class BusMonitor(tasklib.Task):
    def __init__(self):
        tasklib.Task.__init__(self, name="BusMonitor")
        self.data = {}           # Dictionary of bus data

    def run(self):
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.sendto(b"",("localhost",31337))
        while self.runnable:
            msg, addr = sock.recvfrom(8192)
            msg = msg.decode('ascii')
            fields = msg.split(",")
            # Make a dictionary from the update data
            bus = {
               'timestamp' : float(fields[1]),
               'id': fields[2],
               'run' : fields[3],
               'route' : fields[4],
               'lat' : float(fields[5]),
               'lon' : float(fields[6])
            }
            # Save it according to vehicle ID
            self.data[bus['id']] = bus


# dist_bus.py

from socket import socket, AF_INET, SOCK_DGRAM, timeout
import sys
import tasklib

class BusMonitorTask(tasklib.Task):
    def __init__(self,target):
        super(BusMonitorTask,self).__init__(name="busmonitor")
        self.target = target

    # Method that runs in its own thread, updating the buses dictionary
    def run(self):
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.settimeout(5)
        try:
            sock.sendto(b"",("localhost",31337))
            while self.runnable:
                try:
                    msg, addr = sock.recvfrom(8192)
                except timeout:
                    continue
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
                tasklib.send(self.target, ('bus',bus))
        finally:
            sock.close()

import math
import time
from socket import *
from threading import Thread

class BusMonitor:
    def __init__(self):
        self.data = {}           # Dictionary of bus data
        self.thr = Thread(target=self.updater)
        self.thr.daemon = True
        self.thr.start()
    # Method that runs in its own thread, updating the buses dictionary
    def updater(self):
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.sendto(b"",("localhost",31337))
        while True:
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
            self.data.setdefault(bus['id'], []).append(bus)


busses = BusMonitor()
while True:
    time.sleep(1)
    buslist = sorted(busses.data.keys())[:10]
    for busid in buslist:
        bus = busses.data[busid]
        if len(bus) < 2:
            continue
        last, now = bus[-2:]
        distance = math.sqrt((last['lon'] - now['lon']) ** 2 + (last['lat'] - now['lat']) ** 2)
        duration = now['timestamp'] - last['timestamp']
        print(busid, distance/duration)

# asyncbus.py

from socket import *
import ioevent

# An asynchronous bus data monitor
class AsyncBusMonitor(ioevent.IOHandler):
    def __init__(self):
        self.data = {}           # Dictionary of bus data

    # Handshake to the data source
    def handshake(self):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.sendto(b"",("localhost",31337))

    # Expose the socket fileno for the dispatcher
    def fileno(self):
        return self.sock.fileno()

    # We always want to read
    def readable(self):
        return True

    # Callback function triggered whenever data arrives
    def handle_read(self):
        msg, addr = self.sock.recvfrom(8192)
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

# Here is code to run the dispatcher and monitor.
if __name__ == '__main__':
    # Create the event dispatcher
    dispatcher = ioevent.EventDispatcher()

    # Create the bus monitor and register it with the dispatcher
    buses = AsyncBusMonitor()
    buses.handshake()
    dispatcher.register(buses)

    # Run the dispatcher in its own thread.  Note: normally,
    # you would not use a thread here, but I'm doing it so
    # that you can inspect the buses instance as it runs
    import threading
    thr = threading.Thread(target=dispatcher.run)
    thr.daemon = True
    thr.start()

# asyncbusserv.py
#
# An asynchronous bus information server

import socket
import asyncbus
import ioevent
import tcphandler
import geocode
import worker

response_template = """\
<?xml version="1.0"?>
<bus>
   <id>{id}</id>
   <timestamp>{timestamp}</timestamp>
   <run>{run}</run>
   <route>{route}</route>
   <lat>{lat}</lat>
   <lon>{lon}</lon>
   <st>{street}</st>
</bus>
"""

class BusClientHandler(ioevent.IOHandler):
    def __init__(self,busmon,sock,addr,dispatcher):
        self.sock = sock
        self.dispatcher = dispatcher
        self.busmon = busmon
        self.dispatcher.register(self)
        self.busid = None
        self.resp = None

    def fileno(self):
        return self.sock.fileno()

    def readable(self):
        return not self.busid

    def handle_read(self):
        self.busid = self.sock.recv(100).decode('ascii').strip()
        bus = busmon.data.get(self.busid)
        print(bus)
        if bus:
            # Resolve the street name
            wtask = worker.WorkerTask()
            def cb(street=None):
                print('cb')
                self.resp = response_template.format(street=street,**bus)
                self.resp = bytearray(self.resp.encode('ascii'))
                wtask.stop()
            wtask.start()
            fut = wtask.apply(lambda : geocode.streetname(bus['lat'],bus['lon']),
                    callback=cb)
            print("wtask")
        else:
            self.resp = 'unkonown'
            print(self.resp)
            self.resp = bytearray(self.resp.encode('ascii'))

    def writable(self):
        return self.resp

    def handle_write(self):
        self.sock.send(self.resp[:1])
        del self.resp[:1]
        if not self.resp:
            self.sock.close()

class SelfPipe(ioevent.IOHandler):

    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.rsock, self.wsock = socket.socketpair()
        self.wsock.setblocking(False)
        self.dispatcher.register(self)

    def fileno(self):
        return self.rsock.fileno()

    def notify(self):
        self.wsock.send(b'x')

    def readable(self):
        return True

    def writable(self):
        return False

    def handle_read(self):
        self.rsock.recv(1024)

# Code that runs the server (note: no threads)
if __name__ == '__main__':
    import asyncbus
    
    # Create the EventDispatcher
    dispatcher = ioevent.EventDispatcher()
    selfpipe = SelfPipe(dispatcher)

    # Create the bus data monitor handler
    busmon = asyncbus.AsyncBusMonitor()
    busmon.handshake()
    dispatcher.register(busmon)

    # Create and add a TCP server for bus information requests
    tcphandler.TCPServerHandler(("",15000), lambda *args: BusClientHandler(busmon,*args), dispatcher)

    # Run the dispatcher
    dispatcher.run(timeout=0.1)

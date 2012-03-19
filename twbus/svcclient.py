import collections
from twisted.internet import protocol, reactor, task
from twisted.application import service
from twisted.python import log

class BusClientProtocol(protocol.DatagramProtocol):

    def __init__(self, app, host, port):
        self.app = app
        self.host = host
        self.port = port

        # for metrics
        self.recent_timestamps = collections.deque(maxlen=200)

    def startProtocol(self):
        # send an empty packet to the simulator to start receiving data
        self.transport.connect(self.host, self.port)
        self.transport.write("")

    def datagramReceived(self, data, (host, port)):
        fields = data.split(",")
        # Make a dictionary from the update data
        bus = {
            'timestamp' : float(fields[1]),
            'id': fields[2],
            'run' : fields[3],
            'route' : fields[4],
            'lat' : float(fields[5]),
            'lon' : float(fields[6])
        }
        self.app.busdata[bus['id']] = bus
        self.recent_timestamps.append(bus['timestamp'])

    def connectionRefused(self):
        print "No one is listening!"

class ServiceClient(service.Service):

    def __init__(self, app, host, port):
        self.app = app
        self.host = host
        self.port = port
        self.metrics_loop = task.LoopingCall(self.metrics)

    def startService(self):
        self.protocol = BusClientProtocol(self.app, self.host, self.port)
        self.metrics_loop.start(5, now=False)
        reactor.listenUDP(0, self.protocol)

    def stopService(self):
        self.metrics_loop.stop()

    def metrics(self):
        timestamps = self.protocol.recent_timestamps
        if len(timestamps) < 2:
            return
        log.msg('%1.2f messages per second' % ((len(timestamps) - 1) / (timestamps[-1] - timestamps[0])),
                system='ServiceClient')

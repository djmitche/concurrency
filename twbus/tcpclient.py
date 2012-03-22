import json
import collections
from twisted.application import service
from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet import defer
from twisted.internet import endpoints
from twisted.python import failure, log

class ClientProtocol(protocol.Protocol):

    queue_counter = 0

    def connectionMade(self):
        log.msg('incoming client connection from %s' % (self.address,), system='tcpclient')

    def dataReceived(self, data):
        busid = data.strip()

        # invent a new queue id
        self.queue_counter += 1
        return_key = 'client.response.%d' % (self.queue_counter,)

        def cb(key, msg):
            print msg
            if msg:
                self.transport.write(json.dumps(msg) + "\n")
            else:
                self.transport.write('unknown\n')
            self.transport.loseConnection()
            cons.stop_consuming()
        cons = self.app.mq.consume(cb, return_key)
        self.app.mq.produce('db.getid', dict(id=busid, return_key=return_key))

    def connectionLost(self, reason):
        log.msg("lost connection to %s" % (self.address,), system='tcpclient')
        protocol.Protocol.connectionLost(self, reason)


class ClientProtocolFactory(protocol.Factory):

    protocol = ClientProtocol

    def __init__(self, app):
        self.app = app

    def buildProtocol(self, address):
        prot = protocol.Factory.buildProtocol(self, address)
        prot.app = self.app
        prot.address = address
        return prot

class ClientService(service.Service):

    def __init__(self, app, endpoint):
        self.app = app
        self.endpoint = endpoint
        self.startup_d = None

    def startService(self):
        ep = endpoints.serverFromString(reactor, self.endpoint)
        d = self.startup_d = ep.listen(ClientProtocolFactory(self.app))
        @d.addCallback
        def keep_port(port):
            self.port = port

    def stopService(self):
        def stop(_):
            if self.port:
                self.port.stopListening()
        self.startup_d.addCallback(stop)
        return self.startup_d

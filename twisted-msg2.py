import sys
import collections
import struct
from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet import defer
from twisted.internet import endpoints
from twisted.python import failure, log

log.startLogging(sys.stdout)

class MsgProtocol(protocol.Protocol):

    def connectionMade(self):
        self.buf = []
        self.buf_size = 0
        self.broker.addProtocol(self.address, self)
        self.transport.setTcpNoDelay(1)
        self._in_count = 0
        self._out_count = 0

    def dataReceived(self, data):
        self.buf.append(data)
        self.buf_size += len(data)

        # see if we have a full packet
        if self.buf_size < 4:
            return
        data = ''.join(self.buf)
        self.buf = [ data ]

        msglen, = struct.unpack("!I",data[:4])
        total_size = msglen+4
        if self.buf_size < total_size:
            return

        data, self.buf = data[:total_size], [ data[total_size:] ]
        self.buf_size -= total_size

        self.messageReceived(data[4:])

    def messageReceived(self, message):
        self._in_count += 1
        self.broker.messageReceived(self.address, message)

    def sendMessage(self, msg):
        self._out_count += 1
        data = struct.pack("!I", len(msg)) + msg
        self.transport.write(data)

    def connectionLost(self, reason):
        print "lost connection to %s - %d messages received, %d messages sent" % (self.address, self._in_count, self._out_count)
        self.broker.removeProtocol(self.address)
        protocol.Protocol.connectionLost(self, reason)


class MsgProtocolFactory(protocol.Factory):

    protocol = MsgProtocol

    def __init__(self, broker):
        self.broker = broker

    def buildProtocol(self, address):
        prot = protocol.Factory.buildProtocol(self, address)
        prot.broker = self.broker
        prot.address = address
        return prot


class ReplyBroker(object):

    def __init__(self):
        # queue of incoming messages, and a deferred for a pending recv()
        self._incoming_messages = collections.deque()
        self._waiting_recv_d = None

        # current outgoing messages, and a deferred to fire when it is complete
        self._outgoing_addr = None
        self._outgoing_messages = collections.deque()
        self._waiting_send_d = None

        # current state - whether send or recv should be called next
        self._pending_call = 'recv'

        # port/factory handling
        self._factory = MsgProtocolFactory(self)
        self._ports = {}
        self._protocols = {}

    # bind/unbind server endpoings

    @defer.inlineCallbacks
    def bind(self, name):
        endpoint = endpoints.serverFromString(reactor, name)
        self._ports[name] = (yield endpoint.listen(self._factory))

    @defer.inlineCallbacks
    def stop(self):
        for port in self._ports.values():
            yield port.stopListening()

    # handle the comings and goings of protocols

    def addProtocol(self, address, port):
        assert address not in self._protocols
        self._protocols[address] = port
        # it might be time to send a pending message
        self._resolveSends()

    def removeProtocol(self, address):
        del self._protocols[address]

    # REP interface

    def recv(self):
        if self._pending_call != 'recv' or self._waiting_recv_d:
            return failure.Failure(RuntimeError("you jerk"))

        # receive a message from a connected client
        d = defer.Deferred()
        self._waiting_recv_d = d
        self._resolveReceives()
        return d

    def send(self, msg):
        if self._pending_call != 'send' or self._waiting_send_d:
            return failure.Failure(RuntimeError("you jerk"))

        d = defer.Deferred()
        # self._outgoing_addr was set in _resolveReceives
        self._outgoing_messages.appendleft(msg)
        self._waiting_send_d = d
        self._resolveSends()
        return d

    # incoming messages

    def messageReceived(self, addr, msg):
        self._incoming_messages.appendleft((msg, addr))
        self._resolveReceives()

    # move the state machine along

    def _resolveReceives(self):
        # if we have both an incoming message and a deferred to return it with, do so.
        if not self._incoming_messages or not self._waiting_recv_d:
            return

        msg, addr = self._incoming_messages.pop()
        self._outgoing_addr = addr
        self._pending_call = 'send'
        d, self._waiting_recv_d = self._waiting_recv_d, None
        d.callback(msg)

    def _resolveSends(self):
        # if we have a send pending, and the port is present, dooo eeet
        if not self._outgoing_messages:
            return

        # see if that guy is connected
        if self._outgoing_addr not in self._protocols:
            return

        prot = self._protocols[self._outgoing_addr]
        prot.sendMessage(self._outgoing_messages)

        self._pending_call = 'recv'
        d, self._waiting_send_d = self._waiting_send_d, None
        self._outgoing_addr = None
        d.callback(None)

@defer.inlineCallbacks
def serve(brk):
    while True:
        msg = yield brk.recv()
        yield brk.send("GOT:" + msg)

if __name__ == "__main__":
    brk = ReplyBroker()
    brk.bind("tcp:21000")
    def go():
        d = serve(brk)
        d.addCallback(lambda _ : reactor.stop)
        d.addErrback(log.err)
    reactor.callWhenRunning(go)
    reactor.run()

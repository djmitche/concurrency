import struct
from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet import endpoints

class MsgProtocol(protocol.Protocol):

    def connectionMade(self):
        self.buf = []
        self.buf_size = 0

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

        self.messageReceived(data)

    def messageReceived(self, data):
        print data
        return

    def lostConnection(self):
        print "lost connection"

class MsgProtocolFactory(protocol.Factory):

    protocol = MsgProtocol

if __name__ == "__main__":
    endpoint = endpoints.TCP4ServerEndpoint(reactor, 20000)
    endpoint.listen(MsgProtocolFactory())
    reactor.run()

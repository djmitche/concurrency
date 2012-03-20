import json
from twisted.internet import protocol
from twisted.python import log

class BusProtocol(protocol.Protocol):

    def __init__(self): #, transport):
        self.mqConsumers = {}

    def dataReceived(self, frame):
        try:
            request = json.loads(frame)
        except:
            log.msg("invalid JSON from client; terminating", system=self)
            #self.factory.loseConnection()
            return

        try:
            rqType = request.get('type', None)
            if rqType == 'consume':
                topic = request.get('topic')
                if topic and topic not in self.mqConsumers:
                    self.mqConsumers[topic] = \
                            self.factory.app.mq.consume(self.relayMessage, topic)
            elif rqType == 'stop-consuming':
                topic = request.get('topic')
                if topic and topic in self.mqConsumers:
                    self.mqConsumers[topic].stop_consuming()
        except:
            #self.loseConnection()
            raise

    def connectionLost(self, reason):
        log.msg("connection lost", system=self)

    def relayMessage(self, key, message):
        content = json.dumps((key, message))
        self.transport.write(content)


class HandlerFactory(protocol.Factory):

    def __init__(self, app):
        self.app = app

    protocol = BusProtocol

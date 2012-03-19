from twisted.python import log, failure
from twisted.internet import defer
from twisted.application import service

class MQBase(service.Service):

    def __init__(self, app):
        self.setName('mq-implementation')
        self.app = app

    def produce(self, routing_key, data):
        raise NotImplementedError

    def consume(self, callback, *topics, **kwargs):
        raise NotImplementedError

class QueueRef(object):

    __slots__ = [ 'callback' ]

    def __init__(self, callback):
        self.callback = callback

    def invoke(self, routing_key, data):
        if not self.callback:
            return

        try:
            x = self.callback(routing_key, data)
        except Exception:
            log.err(failure.Failure(), 'while invoking %r' % (self.callback,))
            return
        if isinstance(x, defer.Deferred):
            x.addErrback(log.err, 'while invoking %r' % (self.callback,))

    def stop_consuming(self):
        # subclasses should set self.callback to None in this method
        raise NotImplementedError

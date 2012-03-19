from twisted.application import service
from twisted.python.reflect import namedObject

class MQConnector(service.MultiService):

    classes = {
        'simple' : "twbus.mq.simple.SimpleMQ",
    }

    def __init__(self, app, type):
        service.MultiService.__init__(self)
        self.setName('twbus.mq')
        self.app = app
        self.type = type
        self.impl = None # set in setup
        self.impl_type = None # set in setup

    def setup(self):
        assert not self.impl

        # imports are done locally so that we don't try to import
        # implementation-specific modules unless they're required.
        typ = self.type
        assert typ in self.classes # this is checked by MasterConfig
        self.impl_type = typ
        cls = namedObject(self.classes[typ])
        self.impl = cls(self.app)

        # set up the impl as a child service
        self.impl.setServiceParent(self)

        # copy the methods onto this object for ease of access
        self.produce = self.impl.produce
        self.consume = self.impl.consume

    def produce(self, routing_key, data):
        # will be patched after configuration to point to the running
        # implementation's method
        raise NotImplementedError

    def consume(self, callback, *topics, **kwargs):
        # will be patched after configuration to point to the running
        # implementation's method
        raise NotImplementedError

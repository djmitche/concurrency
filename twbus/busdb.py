from twisted.python import log
from twisted.internet import task
from twisted.application import service

class BusDb(service.Service):

    def __init__(self, app):
        self.app = app
        self._data_consumer = None
        self.data = {}
        self.metrics_loop = task.LoopingCall(self.metrics)

    def startService(self):
        self._data_consumer = self.app.mq.consume(self.dataCallback, 'monitor.bus.*')
        self._rpc_consumer = self.app.mq.consume(self.rpcCallback, 'db.getid')
        self.metrics_loop.start(5, now=False)

    def stopService(self):
        self._data_consumer.stop_consuming()
        self._rpc_consumer.stop_consuming()
        self.metrics_loop.stop()

    def dataCallback(self, key, msg):
        self.data[msg['id']] = msg

    def rpcCallback(self, key, msg):
        rv = self.data.get(msg['id'])
        return_key = msg['return_key']
        self.app.mq.produce(return_key, rv)

    def metrics(self):
        log.msg("%d buses in db" % (len(self.data),), system='busdb')

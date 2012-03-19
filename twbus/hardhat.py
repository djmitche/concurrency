from twisted.python import log
from twisted.internet import reactor
from twisted.application import service
from twisted.manhole import telnet

class HardhatService(service.Service):

    tcp_port = 2000
    def __init__(self, app):
        self.app = app

    def startService(self):
        factory = telnet.ShellFactory()
        factory.namespace['app'] = self.app
        factory.username = 'dustin'
        factory.password = 'python'
        self.port = reactor.listenTCP(self.tcp_port, factory)
        log.msg('running on port %d' % (self.tcp_port,), system='hardhat')

    def stopService(self):
        self.port.stopListening()

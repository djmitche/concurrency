from twisted.internet import reactor
from twisted.application import service
from twbus.bussim import bussim

class BusSim(service.Service):

    def __init__(self):
        self.setName('twbus.bussim')

    def setup(self):
        bussim.setup()

    def startService(self):
        assert bussim.runnable, "can't restart bussim"
        self.running_d = reactor.callInThread(bussim.run)

    def stopService(self):
        bussim.runnable = False
        return self.running_d

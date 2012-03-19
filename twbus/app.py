from twisted.application import service
from twbus import streamer, www, hardhat

class BusApp(service.MultiService):

    def __init__(self, svchost, svcport):
        service.MultiService.__init__(self)
        self.setName("twbus")

        self.streamer = streamer.StreamerService(self, svchost, svcport)
        self.streamer.setServiceParent(self)

        self.www = www.WWWService(self)
        self.www.setServiceParent(self)

        self.hardhat = hardhat.HardhatService(self)
        self.hardhat.setServiceParent(self)

        self.busdata = {}

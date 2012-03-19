from twisted.application import service
from twbus import svcclient, www, hardhat

class BusApp(service.MultiService):

    def __init__(self, svchost, svcport):
        service.MultiService.__init__(self)
        self.setName("twbus")

        self.svcclient = svcclient.ServiceClient(self, svchost, svcport)
        self.svcclient.setServiceParent(self)

        self.www = www.WWWService(self)
        self.www.setServiceParent(self)

        self.hardhat = hardhat.HardhatService(self)
        self.hardhat.setServiceParent(self)

        self.busdata = {}

from twisted.application import service
from twbus import monitor, www, hardhat, busdb, tcpclient
from twbus.mq import connector as mqconnector

class BusApp(service.MultiService):

    def __init__(self, svchost, svcport):
        service.MultiService.__init__(self)
        self.setName("twbus")

        self.mq = mqconnector.MQConnector(self, 'simple')
        self.mq.setServiceParent(self)
        self.mq.setup()

        # equiv of busmonitor
        self.monitor = monitor.MonitorService(self, svchost, svcport)
        self.monitor.setServiceParent(self)

        self.www = www.WWWService(self)
        self.www.setServiceParent(self)

        self.busdb = busdb.BusDb(self)
        self.busdb.setServiceParent(self)

        self.tcpclient = tcpclient.ClientService(self, 'tcp:15000')
        self.tcpclient.setServiceParent(self)

        self.hardhat = hardhat.HardhatService(self)
        self.hardhat.setServiceParent(self)

        self.busdata = {}

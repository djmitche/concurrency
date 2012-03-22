# taskdist.py
#
# Support for distributed tasks

from multiprocessing.connection import Client, Listener
import tasklib

class ProxyTask(tasklib.Task):
    def __init__(self,proxyname,target,conn):
        super().__init__(name="proxy")
        self.proxyname = proxyname
        self.target = target
        self.conn = conn
    def run(self):
        try:
            while True:
                msg = self.recv()
                self.conn.send((self.target,msg))
        finally:
            self.conn.close()
            tasklib.unregister(self.proxyname)

# Establish a proxy connection to another machine
def proxy(proxyname,target,address,authkey):
    conn = Client(address,authkey=authkey)
    pxy = ProxyTask(proxyname,target,conn)
    pxy.start()
    tasklib.register(proxyname,pxy)

# Task that receives messages from clients and sends them locally
class DispatchClientTask(tasklib.Task):
    def __init__(self,conn):
        super().__init__(name="dispatchclient")
        self.conn = conn
    def run(self):
        try:
            while True:
                target,msg = self.conn.recv()
                tasklib.send(target,msg)
        finally:
            self.conn.close()

# Task that listens for incoming connections
class DispatcherTask(tasklib.Task):
    def __init__(self,address,authkey):
        super().__init__(name="dispatcher")
        self.address = address
        self.authkey = authkey
    def run(self):
        serv = Listener(self.address,authkey=self.authkey)
        while True:
            try:
                client = serv.accept()
                DispatchClientTask(client).start()
            except Exception as e:
                self.log.info("Error : %s", e, exc_info=True)

_dispatcher = None
def start_dispatcher(address,authkey):
    global _dispatcher
    if _dispatcher:
        return
    _dispatcher = DispatcherTask(address,authkey)
    _dispatcher.start()

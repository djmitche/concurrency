# taskdist.py
#
# Support for distributed tasks

import time
import redis
# Adjust these settings as appropriate
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB   = 0

from multiprocessing.connection import Client, Listener
import tasklib

class ProxyTask(tasklib.Task):

    def __init__(self,proxyname,target,conn,export=True):
        super().__init__(name="proxy", export=export)
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
            if self.export:
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


# Task that receives messages for all unknown targets and creates proxies.                      
class ResolverTask(tasklib.Task):
    CACHE_LIFETIME = 1.0
    def __init__(self,host,port,db,authkey):
        super().__init__(name="resolver")
        self.host = host
        self.port = port
        self.db = db
        self.authkey = authkey
        self.resolver_cache = {}

    def cache_get(self, key):
        if key not in self.resolver_cache:
            return
        v, t = self.resolver_cache[key]
        if t < time.time() - self.CACHE_LIFETIME:
            return
        print("hit")
        return v

    def cache_put(self, key, value):
        print("put")
        self.resolver_cache[key] = (value, time.time())

    def run(self):
        # Establish a connection with the redis server                                          
        r = redis.Redis(host=self.host,port=self.port,db=self.db)
        tasklib.register("resolver",self)
        try:
            while True:
                # Get an outgoing message                                                       
                target, msg = self.recv()

                # Check if a proxy was already registered                                       
                if tasklib.lookup(target):
                    tasklib.send(target,msg)
                    continue

                try:
                    # See if the cache knows anything about the target
                    target_info = self.cache_get(target)

                    # See if redis knows anything about the target                                  
                    if not target_info:
                        target_info = r.get(target)
                        if target_info:
                            self.cache_put(target, target_info)

                    if target_info:
                        host, port = target_info.decode('utf-8').split(":")
                        port = int(port)

                        # Create a proxy task                                                   
                        proxy(target,target,(host,port),self.authkey)
                        self.log.info("Connected to %s", (host,port))

                        # Send the message to the proxy                                         
                        tasklib.send(target,msg)
                    else:
                        self.log.info("Nothing known about target '%s'", target)
                except Exception as e:
                    self.log.info("Couldn't resolve '%s' : %s:%s", target, type(e),e)
        finally:
            tasklib.unregister("resolver")

_resolver = None
def start_resolver(authkey):
    global _resolver
    if _resolver:
        return
    _resolver = ResolverTask(REDIS_HOST, REDIS_PORT, REDIS_DB,authkey)
    _resolver.start()


# Set of all task names that we registered
_registered = set()

# Global task registration.
# Stores a dispatcher (address, authkey) tuple in the registry
def global_register(target):
    if not _dispatcher:
        return
    print("Registering", target)
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    r.set(target,"%s:%d" % _dispatcher.address)
    _registered.add(target)

# Global task unregistration                                                          
def global_unregister(*targets):
    if _dispatcher and targets:
        print("Unregistering", targets)
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        for name in (set(targets) & _registered):
           r.delete(name)
           _registered.remove(name)

# Unregister all tasks at interpreter exit                                            
import atexit
atexit.register(lambda : global_unregister(*_registered))

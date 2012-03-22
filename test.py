import sys
import time
import worker
import geocode
import logging

logging.basicConfig(level=logging.INFO)

from rpcproxy import RPCProxy
proxy = RPCProxy()
proxy.connect(("localhost",22000))
print(proxy.add(2,3))
print(proxy.sub(4,5))
print(proxy.add([1,2,3],[4,5]))


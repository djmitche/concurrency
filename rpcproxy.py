import reqsocket

class RPCFunctionProxy(object):
    def __init__(self, rpcproxy, func_name):
        self.rpcproxy = rpcproxy
        self.func_name = func_name

    def __call__(self, *args, **kwargs):
        self.rpcproxy.send((self.func_name, args, kwargs))
        return self.rpcproxy.recv()

class RPCProxy(reqsocket.RequestSocket):

    def __getattr__(self, name):
        return RPCFunctionProxy(self, name)

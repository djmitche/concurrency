import repsocket

class RPCServer(repsocket.ReplySocket):

    def __init__(self):
        repsocket.ReplySocket.__init__(self)
        self._funcs = {}

    def register_function(self, fn):
        self._funcs[fn.__name__] = fn

    def serve_forever(self):
        while True:
            msg = self.recv()
            func_name, args, kwargs = msg
            res = self._funcs[func_name](*args, **kwargs)
            self.send(res)

# mathserv.py

import rpcserv           # You must write this

def add(x,y):
    return x+y

def sub(x,y):
    return x-y

def mul(x,y):
    return x*y

def div(x,y):
    return x/y

serv = rpcserv.RPCServer()
serv.register_function(add)
serv.register_function(sub)
serv.register_function(mul)
serv.register_function(div)
serv.bind(("",22000))
print("Math server running on port 22000")
serv.serve_forever()

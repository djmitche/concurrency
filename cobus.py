# cobus.py
# 
# Coroutine-based dataflow processing

from socket import *
from coroutine import coroutine

# Produce a stream of messages sent to UDP socket
def produce_messages(sock,maxsize,target):
    while True:
        msg, addr = sock.recvfrom(maxsize)
        target.send(msg)

# Convert a sequence of byte messages to string
@coroutine
def decode_messages(encoding, target):
    while True:
        msg = yield
        target.send(msg.decode(encoding))

# Split a sequence of lines into rows
@coroutine
def splitter(sep, target):
    while True:
        line = yield
        target.send(line.split(sep))

# Turn a sequence of rows into dictionaries
@coroutine
def make_dicts(keys,target):
    while True:
        row = yield
        target.send(dict(zip(keys,row)))

# Printer
@coroutine
def printer():
    while True:
        item = yield
        print(item)

# This requires the bus simulator in Data/bussim.py to be running
if __name__ == '__main__':
    sock = socket(AF_INET, SOCK_DGRAM)
    # Send the handshake
    sock.sendto(b"",("localhost",31337))

    # Stack a collection of coroutines together into a pipeline
    produce_messages(sock, 8192,
                     decode_messages('latin-1',
                     splitter(',',
                     make_dicts(['sequence','time','id','run','route','lat','lon'],
                     printer()))))

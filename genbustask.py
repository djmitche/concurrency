# genbustask.py                                                                                                           

import tasklib

# Generate a stream of messages sent to UDP socket
def gen_udp(sock,maxsize):
    while True:
        msg, addr = sock.recvfrom(maxsize)
        yield msg

# Convert a sequence of byte messages to string
def decode_messages(messages,encoding='latin-1'):
    for msg in messages:
        yield msg.decode(encoding)

# Split a sequence of lines into rows
def splitter(lines,sep=','):
    for line in lines:
        yield line.split(sep)

# Turn a sequence of rows into dictionaries
def make_dicts(rows,keys):
    for row in rows:
        yield dict(zip(keys,row))


class BusDataTask(tasklib.Task):
    def run(self):
        messages = self.generate_messages()
        lines = decode_messages(messages)
        rows = splitter(lines)
        dicts = make_dicts(rows,['sequence','timestamp','id','run','route','lat','lon'])
        for d in dicts:
            print(d)

    def generate_messages(self):
        while True:
            yield self.recv()

if __name__ == '__main__':
    from socket import *

    bustask = BusDataTask()
    bustask.start()

    sock = socket(AF_INET, SOCK_DGRAM)
    sock.sendto(b"",("localhost",31337))
    while True:
        msg,addr = sock.recvfrom(8192)
        bustask.send(msg)


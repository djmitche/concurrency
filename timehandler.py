# timehandler.py

from socket import *
import ioevent
import time

class TimeHandler(ioevent.IOHandler):
    def __init__(self,address):
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.bind(address)
    def fileno(self):
        return self.sock.fileno()
    def readable(self):
        return True
    def handle_read(self):
        msg, addr = self.sock.recvfrom(8192)
        resp = time.ctime().encode('ascii')
        self.sock.sendto(resp,addr)

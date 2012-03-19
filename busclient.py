import sys
from socket import *

s = socket(AF_INET, SOCK_STREAM)
s.connect(("localhost", 15000))
s.send(sys.argv[1].encode('ascii'))
print(s.recv(2048).decode('ascii'))

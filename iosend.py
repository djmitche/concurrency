# iosend.py
from socket import *
msg = b"x"*1024*1024

s = socket(AF_INET, SOCK_STREAM)
s.connect(("localhost",50000))
s.sendall(msg)
s.close()

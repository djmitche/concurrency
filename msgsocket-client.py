import sys
import time
import msgsocket

if __name__ == "__main__":
    body = sys.argv[1]
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect(("localhost",21000))
    msock = msgsocket.MessageSocket(s)
    start = time.time()
    qty = 100000
    for i in range(qty):
        msock.send(body.encode('ascii'))
        msg = msock.recv().decode('ascii')
        assert msg == 'GOT:' + body, msg
    end = time.time()
    print("%s msg/s" % (qty/(end-start)))

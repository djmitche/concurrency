import select
import socket

class SimplexBridge:

    def __init__(self, src, dest):
        self.src = src
        self.dest = dest
        self.buf = bytearray()

    def step(self, r, w, e):
        # return if we can't do anything right now
        if (not self.buf and self.src not in r) or self.dest not in w:
            return

        onemeg = 10 #1024*1024
        if self.src in r:
            while True:
                try:
                    d = self.src.recv(onemeg)
                except socket.error:
                    break
                self.buf += d
                print("%d %s" % (len(d), dir))

        while True:
            try:
                bytes_written = self.dest.send(self.buf)
            except socket.error:
                break
            if bytes_written == 0:
                break
            del self.buf[:bytes_written]
            print("%s %d" % (dir, bytes_written))
        return True

def bridge(s1, s2):

    s1.setblocking(False)
    s2.setblocking(False)
    b1 = SimplexBridge(s1, s2)
    b2 = SimplexBridge(s2, s1)
    while True:
        r, w, e = select.select([s1, s2], [s1, s2], [s1, s2])
        if e:
            break
        if s1 in r and s2 in w:
            if not shovel(s1, s2, ">"):
                break
        if s2 in r and s1 in w:
            if not shovel(s2, s1, "<"):
                break

if __name__ == '__main__':
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
    sock.bind(("",37000))
    sock.listen(1)
    print("Bridge running on port 37000")
    # Get the first client                                                                                      
    client1,addr = sock.accept()
    print("Client 1 connected from", addr)
    client2,addr = sock.accept()
    print("Client 2 connected from", addr)
    print("Bridging clients")
    bridge(client1,client2)

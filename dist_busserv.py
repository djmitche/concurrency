# dist_busserv.py
#
# A server that lets clients inquire about different bus ids

import socket
import tasklib
import sys
import uuid

response_template = """\
<?xml version="1.0"?>
<bus>
   <id>{id}</id>
   <timestamp>{timestamp}</timestamp>
   <run>{run}</run>
   <route>{route}</route>
   <lat>{lat}</lat>
   <lon>{lon}</lon>
</bus>
"""

class ClientTask(tasklib.Task):
    def __init__(self,client_sock,client_addr,busdb_name):
        name = 'client-%s' % uuid.uuid4()
        super(ClientTask,self).__init__(name=name)
        self.client_sock = client_sock
        self.client_addr = client_addr
        self.busdb_name = busdb_name

    def run(self):
        try:
            self.log.info("Client handling connection %s, %s", self.client_sock, self.client_addr)
            self.client_sock.settimeout(5)
            while self.runnable:
                try:
                    busid_bytes = self.client_sock.recv(16)
                except socket.error:
                    return
                except socket.timeout:
                    continue
                if not busid_bytes:
                    break
                busid = busid_bytes.decode('ascii').strip()
                # Send a message to the database task and get the response
                print("sending")
                tasklib.send(self.busdb_name, ('getid',(busid,self.name)))
                print("sent")
                try:
                    print("rxing")
                    tag, bus = self.recv(timeout=10)
                    print("rx'd")
                    if bus:
                        resp = response_template.format(**bus)
                        self.client_sock.send(resp.encode('ascii'))
                        self.client_sock.close()
                    else:
                        self.client_sock.send(b"unknown\n")
                        self.client_sock.close()
                except tasklib.RecvTimeoutError:
                    self.client_sock.send(b"timeout\n")
        finally:
            self.client_sock.close()

class ServerTask(tasklib.Task):
    def __init__(self,server_address,busdb_name):
        super(ServerTask,self).__init__(name="server")
        self.server_address = server_address
        self.busdb_name = busdb_name

    def run(self):
        self.log.info("Server starting on %s", self.server_address)
        serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serv_sock.bind(self.server_address)
        serv_sock.listen(5)
        serv_sock.settimeout(5)
        try:
            while self.runnable:
                try:
                    c,a = serv_sock.accept()
                except socket.timeout:
                    continue
                ClientTask(c,a,self.busdb_name).start()
        finally:
            serv_sock.close()

# To run, use 'python3 dist_busserv.py servport'
if __name__ == '__main__':
    import logging
    import taskdist
    import time

    if len(sys.argv) != 2:
        print("Usage %s: servport")
        raise SystemExit(1)

    servport = int(sys.argv[1])
    
    logging.basicConfig(level=logging.INFO)
    taskdist.start_dispatcher(("localhost",18001),authkey=b"peekaboo")
    taskdist.start_resolver(authkey=b"peekaboo")
    server = ServerTask(("localhost",servport), "busdb")
    server.start()

    # Spin
    while True:
        time.sleep(1)

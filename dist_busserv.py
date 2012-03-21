# dist_busserv.py
#
# A server that lets clients inquire about different bus ids

import socket
import tasklib
import sys

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
    def __init__(self,client_sock,client_addr,busdb):
        super(ClientTask,self).__init__(name="client")
        self.client_sock = client_sock
        self.client_addr = client_addr
        self.busdb = busdb

    def run(self):
        try:
            self.log.info("Client handling connection %s, %s", self.client_sock, self.client_addr)
            self.client_sock.settimeout(5)
            while self.runnable:
                try:
                    busid_bytes = self.client_sock.recv(16)
                except socket.timeout:
                    continue
                if not busid_bytes:
                    break
                busid = busid_bytes.decode('ascii')
                # Send a message to the database task and get the response
                self.busdb.send(('getid',(busid,self)))
                try:
                    tag, bus = self.recv(timeout=10)
                    if bus:
                        resp = response_template.format(**bus)
                        self.client_sock.send(resp.encode('ascii'))
                    else:
                        self.client_sock.send(b"unknown")
                except tasklib.RecvTimeoutError:
                    self.client_sock.send(b"timeout")
        finally:
            self.client_sock.close()

class ServerTask(tasklib.Task):
    def __init__(self,server_address,busdb):
        super(ServerTask,self).__init__(name="server")
        self.server_address = server_address
        self.busdb = busdb

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
                ClientTask(c,a,self.busdb).start()
        finally:
            serv_sock.close()

# To run, use 'python3 -i dist_busserv.py'
if __name__ == '__main__':
    import logging
    import dist_bus
    import dist_busdb

    logging.basicConfig(level=logging.INFO)
    busdb_task = dist_busdb.BusDbTask()
    busdb_task.start()
    busmon_task = dist_bus.BusMonitorTask(target=busdb_task)
    busmon_task.start()
    server = ServerTask(("",15000), busdb_task)
    server.start()

# busserv.py
#
# A simple bus information server

import socket
import bus
import threading

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

def handle_client(client_sock, client_addr, busmon):
    print("Connection from %s" % (client_addr,))
    while True:
        busid_bytes = client_sock.recv(16)
        if not busid_bytes:
            break
        busid = busid_bytes.decode('ascii')
        bus = busmon.data.get(busid)
        if bus:
            resp = response_template.format(**bus[-1])
            client_sock.send(resp.encode('ascii'))
        else:
            client_sock.send(b"unknown")
    print("Connected closed")
    client_sock.close()

def server(server_address,busmon):
    print("Bus Information Server running on", server_address)
    serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serv_sock.bind(server_address)
    serv_sock.listen(5)
    while True:
        c,a = serv_sock.accept()
        thd = threading.Thread(target=lambda : handle_client(c,a,busmon))
        thd.start()

if __name__ == '__main__':
    # Launch the bus data monitor
    buses = bus.BusMonitor()
    # Start the information server
    server(("",15000),buses)

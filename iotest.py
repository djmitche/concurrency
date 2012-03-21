# iotest.py
# 
# A test involving I/O performance

def receive_data(s):
    msg = bytearray()
    while True:
        data = s.recv(1024)
        if not data:
             break
        msg.extend(data)
    return msg

def spin():
    while True:
        pass

if __name__ == '__main__':
    import threading
    import time
    import socket
    
    # Launch a background CPU thread
    if True:
        t = threading.Thread(target=spin)
        t.daemon = True
        t.start()

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
    s.bind(("",50000))
    s.listen(1)
    print("Run iosend.py to send data")
    c,a = s.accept()
    start = time.time()
    msg = receive_data(c)
    end = time.time()
    print(end-start)
    print("{:0.3f} Bytes/sec".format(len(msg)/(end-start)))

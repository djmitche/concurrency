# CTA bus simulator
#
# Author : Dave Beazley (dave@dabeaz.com)
#
# This is a simulator that tries to emulate a stream of GPS data representing
# the positions of CTA city buses.
#
# Tunable parameters:
#
#   TIMESDIR      - Directory of files representing bus position snapshots
#                   (used to supply data to the simulator)
#
#   DELTA         - Period (in seconds) at which new positions are reported
#   INITIAL_TIME  - Initial time at which to start the simulation.
#   RESPONSE_MAX  - Maximum number of response to receive before printing out
#                   the average response time.
#
#   SERVER_PORT   - Port number at which the server listens
#
# Clients receive a stream by sending a UDP message to the given server
# port.  At that point, the simulator feeds a constant stream of 
# updates.    Updates contain the following information:
#
#    SEQUENCE,TIMESTAMP,BUSID,RUN,LATITUDE,LONGITUDE
#

from twisted.python import util

TIMESDIR      = util.sibpath(__file__, "snapshots")
DELTA         = 15.0
INITIAL_TIME  = 1233835569
RESPONSE_MAX  = 250
SERVER_PORT   = 31337

import sys
if len(sys.argv) == 2:
    SERVER_PORT = int(sys.argv[1])

import os
import time
import random
import socket
import threading
import sys
import errno
import gzip

#abspath = os.path.abspath(__file__)
#os.chdir(os.path.dirname(abspath))

# Create a list of all bus times
busfiles       =  os.listdir(TIMESDIR)
times_sequence = [int(name.split(".")[0]) for name in busfiles]
filenames      = sorted([os.path.join(TIMESDIR,name) for t,name in zip(times_sequence,busfiles)
                     if t >= INITIAL_TIME])

times_sequence = times_sequence[-len(filenames):]

# Client address (if any)
client_address = None

# Server socket (if any)
server_sock    = None

# Global sequence number
sequence_number = 0

# Message ack dict
message_ack = { }
last_ack    = -1

# Response time history
response_times = []

def server_thread(port):
    global client_address
    global server_sock
    global sequence_number
    global message_ack, lack_ack
    # Socket server
    server_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    server_sock.setsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF,8192)
    server_sock.bind(("",port))
    while True:
        # Look for a client connection message and set the client_address to that (if any)
        try:
            msg, addr = server_sock.recvfrom(32)
        except socket.error:
            continue
        acktime = time.time()
        if addr == client_address:
            try:
                ackno = int(msg)
                numack = 0
                while last_ack < ackno:
                    last_ack += 1
                    stime = message_ack.pop(last_ack,0.0)
                    numack += 1
                if numack > 1:
                    print("%d updates lost" % (numack-1))
                response_times.append(acktime-stime)
                
                if len(response_times) > 250:
                    print("Average response time : %0.08f" % (sum(response_times)/len(response_times)))
                    print("Active buses", len(active_buses))
                    del response_times[:]

            except ValueError:
                pass
        else:
            print("Setting client to %s" % (addr,))
            client_address  = addr
            message_ack = {}
            last_ack = -1
            sequence_number = 0

# Read bus position data into a dictionary for tracking
def read_positions(filename):
    busdata = {}
    for line in gzip.open(filename):
        line = line.decode('ascii')
        fields = line.split(",")
        rec = {
            'id' : fields[0],
            'run' : fields[1],
            'route' : fields[2],
            'lat' : float(fields[3]),
            'lon' : float(fields[4])
            }
        busdata[fields[0]] = rec
    return busdata

# Delete buses from a set that aren't in the next sequence
def prune_inactive(activebus,nextbus):
    activeids = set(activebus)
    nextids = set(nextbus)
    inactive = activeids - nextids
    inactive_buses = {}
    for id in inactive:
        inactive_buses[id] = activebus.pop(id)

# Compute slope for running to next position
def compute_slopes(activebus,nextbus,delta):
    for id in activebus:
        latm = (nextbus[id]['lat']-activebus[id]['lat'])/delta
        lonm = (nextbus[id]['lon']-activebus[id]['lon'])/delta
        activebus[id]['latm'] = latm
        activebus[id]['lonm'] = lonm

def update_positions(activebus,delta):
    for id in activebus:
        rec = activebus[id]
        rec['lat'] += rec['latm']*delta
        rec['lon'] += rec['lonm']*delta

def setup():
    # need to do this before other service start..
    serv_thr = threading.Thread(target=server_thread,args=(31337,))
    serv_thr.setDaemon(True)
    serv_thr.start()

runnable = True
def run():
    global sequence_number

    # Read the initial buses
    active_buses     = read_positions(filenames[0])
    active_timestamp = times_sequence[0]
    real_timestamp = time.time()

    for i in range(1,len(times_sequence)):
        # Read the next bus set
        next_buses     = read_positions(filenames[i])
        next_timestamp = times_sequence[i]

        # Prune the active bus set for inactive buses
        prune_inactive(active_buses,next_buses)

        # Compute slopes to run to next delta
        compute_slopes(active_buses,next_buses,(next_timestamp-active_timestamp))

        while active_timestamp < next_timestamp:
            # Shift buses to new positions
            update_positions(active_buses,DELTA)
            
            # Create a random sequence of bus ids
            ids = list(active_buses)
            random.shuffle(ids)
            
            # Write a sequence of bus position data on an approximate timer
            interval = DELTA/len(ids)
        
            # Cycle through bus and compute new positions.  Report positions
            first = True
            for id in ids:
                rec = active_buses[id]
                if client_address:
                    timestamp = time.time()
                    message_ack[sequence_number] = timestamp
                    if first:
                        route = "OR"
                        first = False
                    else:
                        route = rec['route']

                    msg = "%d,%s,%s,%s,%s,%s,%s" % (sequence_number,timestamp,id,rec['run'],route,rec['lat'],rec['lon'])
                    server_sock.sendto(msg.encode('ascii'),client_address)
                    sequence_number += 1
                if not runnable:
                    return
                time.sleep(interval)

            active_timestamp += DELTA

        # Shift to the next bus set
        active_buses = next_buses
        active_timestamp = next_timestamp

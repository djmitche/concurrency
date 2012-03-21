# near_thread.py
#
# Find out how long it takes to perform a series of queries
# using a pool of Python threads (as might be in a server)

import sqlite3
import nearstop
import threading
import queue

STOPSDB = "../Concurrent/Data/stops/stops.db"
LOCFILE = "../Concurrent/Data/buslocs.csv"

# Function that runs in its own thread
def performance_test(msg_q):
    db = sqlite3.connect(STOPSDB)
    while True:
        request = msg_q.get()
        if request is None:
            break
        stop = nearstop.nearest_stop(db,*request)
    db.close()
    # Signal other threads about shutdown
    msg_q.put(None)

# Fill the queue with data
def fill_queue(filename,msg_q):
    for n, line in enumerate(open(filename),1):
        fields = line.split(",")
        record = (fields[0],float(fields[1]),float(fields[2]))
        msg_q.put(record)
    msg_q.put(None)
    return n

if __name__ == '__main__':
    import time
    import sys
    if len(sys.argv) != 2:
        print("Usage: %s nthreads" % sys.argv[0])
        raise SystemExit(1)

    nthreads = int(sys.argv[1])

    # Create a queue and populate it with data
    msg_q = queue.Queue()
    nqueries = fill_queue(LOCFILE,msg_q)

    # Create a bunch of threads
    thrs = [threading.Thread(target=performance_test,args=(msg_q,))
            for n in range(nthreads)]

    # Launch the threads and time how long it takes to execute queries
    start = time.time()
    for t in thrs:
        t.start()

    for t in thrs:
        t.join()
    end = time.time()
    print(nqueries,"queries in",end-start,"seconds")
    print(nqueries/(end-start),"queries/sec")

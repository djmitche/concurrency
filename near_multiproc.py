# near_thread.py
#
# Find out how long it takes to perform a series of queries
# using a pool of Python threads (as might be in a server)

STOPSDB = "../Concurrent/Data/stops/stops.db"
LOCFILE = "../Concurrent/Data/buslocs.csv"

import nearstop

# Replacement for the nearest_stop function that uses the opened database
def pool_nearest(route,lat,lon):
    return nearstop.nearest_stop(pool_db,route,lat,lon)

pool_db = None
if __name__ == '__main__':
    import sqlite3
    import multiprocessing

    # Initialize the pool worker by setting up a database connection
    def pool_init():
        global pool_db
        pool_db = sqlite3.connect(STOPSDB)

    pool = multiprocessing.Pool(initializer=pool_init)

import sqlite3
import threading
import queue

# Modified performance test function that uses the pool
def performance_test(pool,msg_q):
    while True:
        request = msg_q.get()
        if request is None:
            break
        stop = pool.apply(pool_nearest,request)    # Do the query
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

    # Create a queue and populate it with data
    msg_q = queue.Queue()
    nqueries = fill_queue(LOCFILE,msg_q)

    # Create a bunch of threads
    thrs = [threading.Thread(target=performance_test,args=(pool, msg_q,))
            for n in range(multiprocessing.cpu_count())]

    # Launch the threads and time how long it takes to execute queries
    start = time.time()
    for t in thrs:
        t.start()

    for t in thrs:
        t.join()
    end = time.time()
    print(nqueries,"queries in",end-start,"seconds")
    print(nqueries/(end-start),"queries/sec")


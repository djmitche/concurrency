# near_single.py
#
# Find out how long it takes to perform a series of queries

import sqlite3
import nearstop

# Edit as appropriate
STOPSDB = "../Concurrent/Data/stops/stops.db"
LOCFILE = "../Concurrent/Data/buslocs.csv"

def performance_test():
    db = sqlite3.connect(STOPSDB)
    for nqueries,line in enumerate(open(LOCFILE),1):
        fields = line.split(",")
        stop = nearstop.nearest_stop(db, fields[0],float(fields[1]),float(fields[2]))
    db.close()
    return nqueries

if __name__ == '__main__':
    import time
    start = time.time()
    nqueries = performance_test()
    end = time.time()
    print(nqueries,"queries in",end-start,"seconds")
    print(nqueries/(end-start),"queries/sec")

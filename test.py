import sys
import time
import worker
import geocode
import logging

logging.basicConfig(level=logging.INFO)

pool = worker.WorkerPool(8)

pool.start()
results = [pool.apply(geocode.streetname,(41.8007,-87.7297))
                                for n in range(8)]
for r in results:
    print(r.get())       

pool.stop()

time.sleep(1)

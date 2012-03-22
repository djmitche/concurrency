# dist_busdb.py
import time
import tasklib
import copy

class BusDbTask(tasklib.Task):
    def __init__(self):
        super(BusDbTask,self).__init__(name="busdb")
        self.data = {}           # Dictionary of bus data

    # Receive messages and update the buses dictionary
    def run(self):
        while True:
            tag, msg = self.recv()
            # If 'bus' message, update the internal dictionary
            if tag == 'bus':
                bus = msg
                self.data[bus['id']] = bus
            # If 'getid' message, get the busid and target for response data
            elif tag == 'getid':
                busid, target = msg
                bus = self.data.get(busid)
                time.sleep(1)
                tasklib.send(target, ('bus',copy.deepcopy(bus)))

if __name__ == '__main__':
    import taskdist
    import logging
    import time

    logging.basicConfig(level=logging.INFO)

    # Start the dispatcher                                                                      
    taskdist.start_dispatcher(("localhost",18000),authkey=b"peekaboo")
    taskdist.start_resolver(authkey=b"peekaboo")

    busdb_task = BusDbTask()
    busdb_task.start()
    tasklib.register("busdb",busdb_task,export=True)

    while True:
        time.sleep(1)

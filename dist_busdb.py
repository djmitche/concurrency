# dist_busdb.py
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
                tasklib.send(target, ('bus',copy.deepcopy(bus)))

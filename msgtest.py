# msgtest.py                                                                                                       

import tasklib
class MsgTestTask(tasklib.Task):
    def run(self):
        while True:
             msg = self.recv()       # Got a message                                                               
             print("Got:", msg)

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    msgtask = MsgTestTask()
    msgtask.start()

    # Now try sending various messages                                                                             
    msgtask.send("Hello World")
    msgtask.send(42)
    for n in range(10):
        msgtask.send(n)

    # Shut it down                                                                                                 
    msgtask.stop(wait=True)

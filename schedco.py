# schedco.py
#
# A coroutine-based messaging system loosely based on actors.

from queue import Queue

# Dictionary mapping task names to coroutines
tasks = { }

# Queue of runnable tasks and pending messages
task_queue = Queue()

# Register a new coroutine
def register(name, task):
    tasks[name] = task

# Send a message to a task
def send(name,msg):
    task = tasks.get(name)
    if task:
        # Put the task and message on queue
        task_queue.put((task,msg))

# Run all tasks
def scheduler():
    while not task_queue.empty():
        # Get the next task and message
        task, msg = task_queue.get()
        # Send the message to the task
        try:
            task.send(msg)
        except StopIteration:
            pass

if __name__ == '__main__':
    from coroutine import coroutine

    @coroutine
    def printer():
        while True:
            msg = yield
            print(msg)

    @coroutine
    def ping():
        while True:
            msg = yield      
            send("printer",msg)
            send("pong","Hello from ping")

    @coroutine
    def pong():
        while True:
            msg = yield 
            send("printer",msg)
            send("ping","Hello from pong")

    register("printer", printer())
    register("pong",pong())
    register("ping",ping())
    # Send an initial message to initiate execution
    send("ping","starting")
    # Run the scheduler
    scheduler()

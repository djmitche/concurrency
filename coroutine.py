# coroutine.py

def coroutine(func):
    def start(*args,**kwargs):
        r = func(*args,**kwargs)
        next(r)
        return r
    return start

import re
import pprint
from twisted.python import log
from twbus.mq import base

class SimpleMQ(base.MQBase):

    def __init__(self, app):
        base.MQBase.__init__(self, app)
        self.qrefs = []
        self.persistent_qrefs = {}
        self.debug = False

    def produce(self, routing_key, data):
        if self.debug:
            log.msg("MSG: %s\n%s" % (routing_key, pprint.pformat(data)), system='mq')
        for qref in self.qrefs:
            if qref.matches(routing_key):
                qref.invoke(routing_key, data)

    def consume(self, callback, *topics, **kwargs):
        persistent_name = kwargs.get('persistent_name', None)
        if persistent_name:
            if persistent_name in self.persistent_qrefs:
                qref = self.persistent_qrefs[persistent_name]
                qref.start_consuming(callback)
            else:
                qref = PersistentQueueRef(self, callback, topics)
                self.qrefs.append(qref)
                self.persistent_qrefs[persistent_name] = qref
        else:
            qref = QueueRef(self, callback, topics)
            self.qrefs.append(qref)
        return qref

class QueueRef(base.QueueRef):

    __slots__ = [ 'mq', 'topics' ]

    def __init__(self, mq, callback, topics):
        base.QueueRef.__init__(self, callback)
        self.mq = mq
        self.topics = [ self.topic_to_re(t) for t in topics ]

    def topic_to_re(self, topic):
        subs = { '.' : r'\.', '*' : r'[^.]+', }
        needs_quotes_re = re.compile(r'([\\.*?+{}\[\]|()])')

        parts = re.split(r'(\.)', topic)
        topic_re = []
        while parts:
            part = parts.pop(0)
            if part in subs:
                topic_re.append(subs[part])
            elif part == '#':
                if parts:
                    # pop the following '.', as it will not exist when
                    # matching zero words.
                    parts.pop(0)
                    topic_re.append(r'([^.]+\.)*')
                else:
                    # pop the previous '.' from the regexp, as it will not
                    # exist when matching zero words
                    if topic_re:
                        topic_re.pop()
                        topic_re.append(r'(\.[^.]+)*')
                    else:
                        # topic is just '#': degenerate case
                        topic_re.append(r'.+')
            else:
                topic_re.append(needs_quotes_re.sub(r'\\\1', part))
        topic_re = ''.join(topic_re) + '$'
        return re.compile(topic_re)

    def matches(self, routing_key):
        for re in self.topics:
            if re.match(routing_key):
                return True
        return False

    def stop_consuming(self):
        self.callback = None
        try:
            self.mq.qrefs.remove(self)
        except ValueError:
            pass

class PersistentQueueRef(QueueRef):

    __slots__ = [ 'active', 'queue' ]

    def __init__(self, mq, callback, topics):
        QueueRef.__init__(self, mq, callback, topics)
        self.queue = []

    def start_consuming(self, callback):
        self.callback = callback
        self.active = True

        # invoke for every message that was missed
        queue, self.queue = self.queue, []
        for routing_key, data in queue:
            self.invoke(routing_key, data)

    def stop_consuming(self):
        self.callback = self.add_to_queue
        self.active = False

    def add_to_queue(self, routing_key, data):
        self.queue.append((routing_key, data))

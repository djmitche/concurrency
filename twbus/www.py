import json
from twisted.python import log, util
from twisted.internet import defer
from twisted.web import resource, server, static
from twisted.application import strports, service
from twbus import websocket # from Twisted bug 4173
from twbus import ws

class WWWService(service.MultiService):

    def __init__(self, app):
        service.MultiService.__init__(self)
        self.setName('twbus.www')
        self.app = app

        self.port = 8010

        self.root = RootResource(self.app)

        self.site = server.Site(self.root)

        port = "tcp:%d" % self.port if type(self.port) == int else self.port
        self.port_service = strports.service(port, self.site)
        self.port_service.setServiceParent(self)

class Resource(resource.Resource):

    contentType = 'text/html'

    def __init__(self, app):
        resource.Resource.__init__(self)
        self.app = app

    def render(self, request):
        d = defer.maybeDeferred(lambda : self.content(request))
        def handle(data):
            if isinstance(data, unicode):
                data = data.encode("utf-8")
            request.setHeader("content-type", self.contentType)
            if request.method == "HEAD":
                request.setHeader("content-length", len(data))
                return ''
            return data
        d.addCallback(handle)
        def ok(data):
            request.write(data)
            try:
                request.finish()
            except RuntimeError:
                # this occurs when the client has already disconnected; ignore
                # it (see #2027)
                log.msg("http client disconnected before results were sent", system='www')
        def fail(f):
            request.processingFailed(f)
            return None # processingFailed will log this for us
        d.addCallbacks(ok, fail)
        return server.NOT_DONE_YET

    def content(self, request):
        return ''

    def json(self, value):
        return json.dumps(value, sort_keys=True, indent=4)


class RootResource(Resource):

    def __init__(self, app):
        Resource.__init__(self, app)
        self.putChild('api', ApiResource(app))
        self.putChild('ws', websocket.WebSocketsResource(ws.HandlerFactory(app)))
        self.putChild('ui', static.File(util.sibpath(__file__, 'ui')))


class ApiResource(Resource):

    def __init__(self, app):
        Resource.__init__(self, app)
        self.putChild('bus', BussesResource(app))


class BussesResource(Resource):

    def getChild(self, name, request):
        try:
            busid = str(int(name))
        except (TypeError, ValueError):
            return Resource.getChild(self, name, request)
        if busid not in self.app.busdata:
            return Resource.getChild(self, name, request)
        return BusResource(self.app, busid)

    def content(self, request):
        return self.json([ dict(id=busid, url='/api/bus/%s' % busid)
                            for busid, bus in sorted(self.app.busdata.items())
                            ])

class BusResource(Resource):

    def __init__(self, app, busid):
        Resource.__init__(self, app)
        self.app = app
        self.busid = busid

    def content(self, request):
        bus = self.app.busdata[self.busid]

        return self.json(bus)

# restserv.py
#
# Skeleton of a bare-bones REST server

import json
import re
import geocode
from http.server import HTTPServer, BaseHTTPRequestHandler

class RESTRequestHandler(BaseHTTPRequestHandler):
    latlong_re = re.compile("/([^,]*),(.*)$")
    def do_GET(self):
        print(self.path)
        lat, lon = self.latlong_re.match(self.path).groups()
        st = geocode.streetname(lat, lon)
        
        # Send a response
        self.send_response(200)
        self.send_header('content-type','text/plain')
        self.end_headers()
        self.wfile.write(json.dumps(st).encode('utf-8'))

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Usage: %s port" % sys.argv[0])
        raise SystemExit(1)
    
    port = int(sys.argv[1])
    serv = HTTPServer(("",port), RESTRequestHandler)
    serv.serve_forever()

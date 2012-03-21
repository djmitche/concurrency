# geocode.py
import urllib.request
import json
import io

def streetname(lat,lon):
    u = urllib.request.urlopen("http://www.dabeaz.com/cgi-bin/geo.py?q=%s,%s" % (lat,lon))
    doc = json.load(io.TextIOWrapper(u,encoding='utf-8'))
    return doc['Placemark'][0]['address']

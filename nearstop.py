# nearstop.py
#
# Function that finds the nearest bus stop to a give route, lat, lon coordinate

def nearest_stop(db,route,lat,lon):
    stops = list(db.execute("select * from stops where route=? "
                            "order by (abs(lat-?)+abs(lon-?)) limit 1",
                            (route,lat,lon)))
    return stops[0] if stops else None

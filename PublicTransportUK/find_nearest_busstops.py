# -*- coding: utf-8 -*-
"""
Created on Mon 27 June 2016

@author: Ahmad
"""

import pymongo
from bson.son import SON
import json
from bson import json_util
from bson.json_util import dumps
import sys
import csv

def establish_connection_optimum(db_name):
    try:
        # establish a connection to the collection
        host = "optimum.euprojects.net"
        port = 3368
        db = db_name
        user = ''
        password = ''
        connection = pymongo.MongoClient(host, port)
#        connection[db].authenticate(user, password)
        return connection[db]
    
    except Exception, e:
        print(e)
        sys.exit()

def fetch_nearest_atcocodes(db,limit,lon,lat):
    atcocodes = []
    lons =[]
    lats = []
    try:
        for result in db.command(SON([("geoNear", "busStopsBirm"),("near", [lon, lat]),
                                       ("spherical", True),("limit",limit)]))["results"]:
    #         print dumps(result, indent=2, default=json_util.default)
            atcocodes.append(result['obj']['ATCOCode'])
            lons.append(result['obj']['loc']['coordinates'][0])
            lats.append(result['obj']['loc']['coordinates'][1])
    except Exception, e:
        print(e)
        sys.exit()
    
    f = open("nearest_stops.csv", "wb")
    try:
        lines = []
        for i in range(0,len(atcocodes)):
            line = '{},{},{}'.format(atcocodes[i],lons[i],lats[i])
            #print line
            lines.append(line)
            
        w = csv.writer(f, delimiter = ',')
        w.writerows([x.split(',') for x in lines])
    except Exception, e:
        print(e)
        sys.exit() 
    f.close()

if __name__ == '__main__':
    db = establish_connection_optimum("PublicTransportUK")
    limit = 20
    lon = -1.8904
    lat = 52.4862
    fetch_nearest_atcocodes(db,limit,lon,lat)
    
    
    
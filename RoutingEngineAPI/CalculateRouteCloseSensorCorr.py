# -*- coding: utf-8 -*-
"""
Created on Thu Jun 09 14:43:20 2016

@author: Ahmad
"""

import requests
import json
import pyproj
import urllib2
import urllib
from bson.json_util import dumps
from bson import json_util
import sys
import pymongo
from bson.son import SON
import operator
import time
import pandas as pd
from pytz import timezone
import datetime
import logging
import sys
import matplotlib.pyplot as plt
import numpy as np

def establish_connection_optimum_collection(db_name, collection_name):
    try:
        # establish a connection to the collection
        host = "optimum.euprojects.net"
        port = 3368
        db = db_name
        user = ''
        password = ''
        collection = collection_name
        connection = pymongo.MongoClient(host, port)
#        connection[db].authenticate(user, password)
        return connection[db][collection]
    
    except Exception, e:
        print(e)
        sys.exit()
        
def geocode_address(address):
    coordinates = {}
    encoded_loc = urllib.quote(address)
    url = 'http://nominatim.openstreetmap.org/search?format=json&q=' + encoded_loc
    try:
        data = json.load(urllib2.urlopen(url))
    except Exception, e:
        print(e)
        sys.exit()
    #Print for testing
#    print dumps(data[0], indent=2, default=json_util.default)
    
    if len(data) > 0:
        try:
            coordinates['lon'] = data[0]['lon']
            coordinates['lat'] = data[0]['lat']
        
        except Exception, e:
            print(e)
            sys.exit()
        return coordinates
    
    else:
        return "No lon/lat found"
        
def get_route_id(source_co, dest_co):
    #send the post request to get the route id
    url = 'http://62.218.45.10:8080/optimum/routes'
    payload = {
        "serviceId" : "at.ac.ait.optimum",
        "from" : {
          "type" : "Location",
          "coordinate" : {
            "type" : "Feature",
            "geometry" : { "type" : "Point", "coordinates" : [ source_co['lon'], source_co['lat'] ] },
          }
        },
        "to" : {
          "type" : "Location",
          "coordinate" : {
            "type" : "Feature",
            "geometry" : { "type" : "Point", "coordinates" : [ dest_co['lon'], dest_co['lat'] ] },
          }
        },
        "modesOfTransport" : [ "FOOT" ],
        "optimizedFor" : "traveltime"
    }
    headers = {'content-type': 'application/json'}
    try:
        r = requests.post(url, data=json.dumps(payload), headers=headers)
    except Exception, e:
        print(e)
        sys.exit()
#    print dumps(r.headers, indent=2, default=json_util.default)
        
    if "Location" in r.headers.keys():
        return r
    else:
        print "No route returned" 
        sys.exit()
    
def get_route_data(routeid, max_sensors, no_points_to_show):
    if routeid != -1:
        try:
            data = json.load(urllib2.urlopen(routeid))
        except Exception, e:
            print(e)
            sys.exit()
#        print dumps(data, indent=2, default=json_util.default)
        if isinstance(data, dict):
            route = data['routes'][0]
            segment = route['segments'][0]
            coordinates = segment['geometryGeoJson']['geometry']['coordinates']
#            print len(coordinates)
            get_sensors_by_distance_pyproj(coordinates, max_sensors, no_points_to_show)
        else:
            print "No content found"
            sys.exit()
            
def get_sensors_by_distance_pyproj(coordinates, max_sensors, no_points_to_show):
    #for every point, get the closest 3 sensor ids and their distances (pyproj library)
    t0 = time.time()
    geod = pyproj.Geod(ellps="WGS84")
    sensor_coors = {}
    collection = establish_connection_optimum_collection("BccTraffic","roadSensor")
#    query = {"dataSource" : "BCC"}
    query = {}
    cursor = collection.find(query)
    for doc in cursor:
        sensor_coors[doc['measurement_id']] = doc['loc']['coordinates']
    point_sensor_dists = []
    for coors in coordinates:
        distances = {}
        for sensor in sensor_coors.keys():
            angle1,angle2,distance = geod.inv(coors[0], coors[1], sensor_coors[sensor][0], sensor_coors[sensor][1])
            distances[sensor] = distance
        point_sensor_dists.append(distances)
#           print dumps(result, indent=2, default=json_util.default)
    point_closest_sens_ids = []
    point_closest_sens_dists = []
    for sensors_distances in point_sensor_dists:
        sorted_x = sorted(sensors_distances.items(), key=operator.itemgetter(1), reverse=False)
        counter = 0
        closest_sens_ids = []
        closest_sens_dists = []
        for sensor_id, dist in sorted_x:
            if counter < max_sensors:
                closest_sens_ids.append(sensor_id)
                closest_sens_dists.append(dist)
                counter += 1
            else:
                break
        point_closest_sens_ids.append(closest_sens_ids)
        point_closest_sens_dists.append(closest_sens_dists)
    t1 = time.time()
    timeDiff = t1-t0
#    for i in range(0,no_points_to_show):
#        print point_closest_sens_ids[i]
#        print point_closest_sens_dists[i]
    print "Finihsed getting closed sensors. Time (sec): %s\n" % (timeDiff)
    
    return point_closest_sens_ids[0:no_points_to_show]
    
def computeCorrsDists(closeSensorIds):
    m_type = 'AverageSpeed'
    sensor_collection = establish_connection_optimum_collection("BccTraffic", "roadSensorValue")
    for closeSensorId in closeSensorIds:
        measurements = fetch_measurements(sensor_collection, closeSensorId, m_type)
        compute_correlations(measurements)
    
def main(source,destination,max_sensors,no_points_to_show):
    source_co = geocode_address(source)
    dest_co = geocode_address(destination)
    r = get_route_id(source_co, dest_co,)
    closeSensorIdsLst = get_route_data(r.headers['Location'], max_sensors, no_points_to_show)
    coooDistsDF = computeCorrsDists(closeSensorIdsLst)
    
    
if __name__ == '__main__':
    source = '44 Oldfield Road Birmingham West Midlands B12 8TY UK'
    destination = '50 Avenue Road Birmingham West Midlands B6 4DY UK'
    no_points_to_show = 10
    max_sensors = 20
    main(source,destination,max_sensors,no_points_to_show)
            

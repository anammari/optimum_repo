# -*- coding: utf-8 -*-
"""
Created on Thu Feb 18 2016

@author: Ahmad

Objectives: 
    - Retrieve JSON data from BCC API Endpoints 
    - Process the data to match the transformed traffic structure
    - Insert the data records into mongoDB collections
"""

from datetime import datetime
from time import gmtime, strftime
import sys
#sys.path.append('/Users/ahmadammari/Dropbox/Work/Optimum/bcc/bcc_streaming/ENtoLL.py')
sys.path.append('C:\\Users\\Optimum\\Documents\\bcc\\bcc_streaming\\ENtoLL.py')
import ENtoLL
import json
import pytz
from pytz import timezone
from bson import json_util
import pymongo
import urllib2
import urllib
import logging

#logfile = '/Users/ahmadammari/Dropbox/Work/Optimum/bcc/bcc_streams.log'
logfile = 'C:\\Users\\Optimum\\Documents\\bcc\\bcc_streams.log'
logging.basicConfig(filename=logfile,level=logging.INFO, format='%(asctime)s %(message)s')

def establish_connection_optimum(collection_name):
    try:
        # establish a connection to the tw_hashtags collection
        host = "euprojects.net"
        port = 3368
        db = 'BCC_traffic'
        user = ''
        password = ''
        collection = collection_name
        connection = pymongo.MongoClient(host, port)
#        connection[db].authenticate(user, password)
        #Drop collection if exists
        if collection in connection[db].collection_names():
            connection[db][collection].drop()
        return connection[db][collection]
    
    except Exception, e:
		print(e)
		sys.exit()

def establish_connection_local(collection_name):
    try:
        # establish a connection to the tw_hashtags collection
        host = 'localhost'
        port = 27017
        db = 'BCC_traffic'
        user = ''
        password = ''
        collection = collection_name
        connection = pymongo.MongoClient(host, port)
#        connection[db].authenticate(user, password)
        #Drop collection if exists
        if collection in connection[db].collection_names():
            connection[db][collection].drop()
        return connection[db][collection]
    
    except Exception, e:
		print(e)
		sys.exit()
      
def read_bcc_traffic(measurement):
    gmt = timezone('GMT')
    try:
        if "ies" not in measurement:
            url = 'http://butc.opendata.onl/AL_OpenData/%s.json' % (measurement[:-1])
        else:
            url = 'http://butc.opendata.onl/AL_OpenData/%s.json' % (measurement[:-3]+"y")
        data = json.load(urllib2.urlopen(url))
    except Exception, e:
		print(e)
		sys.exit()
    return data
    
    #print the data object
#    print json.dumps(data, indent=2, default=json_util.default)
  
def process_bcc_traffic(measurement,data):
    gmt = timezone('GMT')
    records = []
    try:
        if "ies" not in measurement:
            m_list = data[measurement][measurement[:-1]]
            m_type = str(measurement[:-1])
        else:
            m_list = data[measurement][measurement[:-3]+"y"]
            m_type = str(measurement[:-3]+"y")
        for m in m_list:
            record = {}
            record["type"] = m_type
            record["typeSensor"] = str(m["Type"])
            record["measurement_id"] = str(m["SCN"])
            record["description"] = str(m["Description"])
            record["status"] = str(m["Value"]["Status"])
            (longi,lati) = ENtoLL.ENtoLL84(float(m["Easting"]), float(m["Northing"]))
            record["measurement_datetime"] = datetime.strptime(m["LastUpdated"], '%Y-%m-%d %H:%M:%S')
            record["value"] = int(m["Value"]["Percent"]["Value"])
            record["lane"] = "all"
            record["VehicleCategory"] = "all"
            record["trend"] = str(m["Value"]["Trend"])
            loc = {
                "type" : "Point",
                "coordinates" : [float(longi), float(lati)]
            }            
            record["loc"] = loc
            dt = datetime.now()
            gmt_dt = gmt.localize(dt)
            record["insertion_datetime"] = gmt_dt
            records.append(record)
    except Exception, e:
        print(e)
        sys.exit()
    return records

def add_bcc_traffic_local(measurement,records):
    try:
        collection = establish_connection_local(measurement)
#        for record in records:
#            collection.insert(record)
        
        if len(records) > 0:
            collection.insert_many(records)
            
        msg = ",%s,%s" % (measurement, str(len(records)))
        logging.info(msg)
        
    except Exception, e:
        print(e)
        sys.exit()

def add_bcc_traffic_optimum(measurement,records):
    try:
        collection = establish_connection_optimum(measurement)
#        for record in records:
#            collection.insert(record)
        
        if len(records) > 0:
            collection.insert_many(records)      
        
        msg = ",%s,%s" % (measurement, str(len(records)))
        logging.info(msg)        
        
    except Exception, e:
        print(e)
        sys.exit()

def push_bcc_data_to_mongo_local(measurement):
    try:
        data = read_bcc_traffic(measurement)
        records = process_bcc_traffic(measurement,data)
        add_bcc_traffic_local(measurement,records)
    except Exception, e:
        print(e)
        sys.exit()

def push_bcc_data_to_mongo_optimum(measurement):
    try:
        data = read_bcc_traffic(measurement)
        records = process_bcc_traffic(measurement,data)
        add_bcc_traffic_optimum(measurement,records)
    except Exception, e:
        print(e)
        sys.exit()
            
if __name__ == '__main__':
    push_bcc_data_to_mongo_optimum("Flows") 
    push_bcc_data_to_mongo_optimum("AverageSpeeds")
#    push_bcc_data_to_mongo_local("TravelTimes")
#    push_bcc_data_to_mongo_local("Congestions")
#    push_bcc_data_to_mongo_local("Occupancies")
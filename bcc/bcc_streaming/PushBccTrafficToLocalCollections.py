# -*- coding: utf-8 -*-
"""
Created on Thu Feb 18 2016

@author: Ahmad

Objectives: 
    - Check if the BCC Collections exist, if no refresh and database by calling the URLs 
    - If yes, call the URLs, query the DB to get the sensors with their latest records, and insert the new records 
"""

from datetime import datetime
import time
import sys
#sys.path.append('/Users/ahmadammari/Dropbox/Work/Optimum/bcc/bcc_streaming/ENtoLL.py')
sys.path.append('C:\\Users\\Optimum\\Documents\\bcc\\bcc_streaming\\ENtoLL.py')
import ENtoLL
import json
import pytz
from pytz import timezone
from bson import json_util
from bson.json_util import dumps
import pymongo
import urllib2
import urllib
#sys.path.append('/Users/ahmadammari/Dropbox/Work/Optimum/bcc/bcc_streaming/pushBccDataToMongoFirstTime.py')
sys.path.append('C:\\Users\\Optimum\\Documents\\bcc\\bcc_streaming\\pushBccDataToMongoFirstTime.py')
import pushBccDataToMongoFirstTime
#sys.path.append('/Users/ahmadammari/Dropbox/Work/Optimum/bcc/bcc_streaming/pushBccAnprToMongoFirstTime.py')
sys.path.append('C:\\Users\\Optimum\\Documents\\bcc\\bcc_streaming\\pushBccAnprToMongoFirstTime.py')
import pushBccAnprToMongoFirstTime
from bson.son import SON
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
        return connection[db][collection]
    
    except Exception, e:
		print(e)
		sys.exit()

def get_collections_names_optimum(db):
    try:
        # establish a connection to the tw_hashtags collection
        host = 'euprojects.net'
        port = 3368
        user = ''
        password = ''
        connection = pymongo.MongoClient(host, port)
#        connection[db].authenticate(user, password)
        return connection[db].collection_names()
    
    except Exception, e:
		print(e)
		sys.exit()

def get_collections_names_local(db):
    try:
        # establish a connection to the tw_hashtags collection
        host = 'localhost'
        port = 27017
        user = ''
        password = ''
        connection = pymongo.MongoClient(host, port)
#        connection[db].authenticate(user, password)
        return connection[db].collection_names()
    
    except Exception, e:
		print(e)
		sys.exit()

def refresh_bcc_collections_local(collection):
    if collection == 'ANPR':
        pushBccAnprToMongoFirstTime.push_bcc_data_to_mongo_local(collection)
    else:
        pushBccDataToMongoFirstTime.push_bcc_data_to_mongo_local(collection)
    
def refresh_bcc_collections_optimum(collection):
    if collection == 'ANPR':
        pushBccAnprToMongoFirstTime.push_bcc_data_to_mongo_local(collection)
    else:
        pushBccDataToMongoFirstTime.push_bcc_data_to_mongo_local(collection)
    
def get_records_by_sensor_id_and_last_datetime(collection):
    try:
        pipeline = [
              { "$group": {
              "_id": {
                "sensor_id": "$measurement_id",
                     },   
              "count": { "$sum": 1 },
              "last": {"$max": "$measurement_datetime"} 
                          }
              },
              { "$sort": {"_id": -1}},  
              { "$project": { "last": "$last", "count": 1, "_id": 1} }
        ]
        cursor = collection.aggregate(pipeline)
    except Exception, e:
		print(e)
		sys.exit()
    #Print for testing
#    print dumps(cursor, indent=2, default=json_util.default)
    
    latest_readings = {}
    try:    
        for doc in cursor:
            latest_readings[doc["_id"]["sensor_id"]] = doc["last"]
    except Exception, e:
		print(e)
		sys.exit()
  
    return latest_readings
    
def read_bcc_traffic(measurement):
    gmt = timezone('GMT')
    try:
        if measurement != "ANPR":
            if "ies" not in measurement:
                url = 'http://butc.opendata.onl/AL_OpenData/%s.json' % (measurement[:-1])
            else:
                url = 'http://butc.opendata.onl/AL_OpenData/%s.json' % (measurement[:-3]+"y")
            data = json.load(urllib2.urlopen(url))
        else:
            url = 'http://butc.opendata.onl/AL_OpenData/%s.json' % (measurement)
            data = json.load(urllib2.urlopen(url))
    except Exception, e:
		print(e)
		sys.exit()
    return data
    
    #print the data object
#    print json.dumps(data, indent=2, default=json_util.default)
  
def process_bcc_traffic(measurement, data, latest_readings):
    gmt = timezone('GMT')
    records = []
    try:
        if measurement != "ANPR": 
            if "ies" not in measurement:
                m_list = data[measurement][measurement[:-1]]
                m_type = str(measurement[:-1])
            else:
                m_list = data[measurement][measurement[:-3]+"y"]
                m_type = str(measurement[:-3]+"y")
            for m in m_list:
                measurement_datetime = datetime.strptime(m["LastUpdated"], '%Y-%m-%d %H:%M:%S')
                if str(m["SCN"]) in latest_readings.keys():
                    if measurement_datetime > latest_readings[str(m["SCN"])]:
                        record = generate_data_record(m, m_type)
                        records.append(record)
                else:
                    record = generate_data_record(m, m_type)
                    records.append(record)
        else:
            m_list = data["UTMC_" + measurement][measurement]
            for m in m_list:
                measurement_datetime = datetime.strptime(m["LastUpdated"], '%Y-%m-%d %H:%M:%S')
                if str(m["SCN"]) in latest_readings.keys():
                    if measurement_datetime > latest_readings[str(m["SCN"])]:
                        anprrecords = generate_anpr_records(m)
                        for record in anprrecords:
                            records.append(record)
                else:
                    anprrecords = generate_anpr_records(m)
                    for record in anprrecords:
                        records.append(record)
    except Exception, e:
        print(e)
        sys.exit()
    return records

def generate_data_record(m, m_type):
    try:
        gmt = timezone('GMT')
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
    
    except Exception, e:
        print(e)
        sys.exit()
    
    return record

def generate_anpr_records(m):
    try:
        gmt = timezone('GMT')
        anprrecords = []
        #TravelTime            
        record = {}
        record["type"] = "TravelTime"
        record["typeSensor"] = "ANPR"
        record["measurement_id"] = str(m["SCN"])
        record["description"] = str(m["Description"])
        record["status"] = None
        (longi,lati) = ENtoLL.ENtoLL84(float(m["Easting"]), float(m["Northing"]))
        record["measurement_datetime"] = datetime.strptime(m["LastUpdated"], '%Y-%m-%d %H:%M:%S')
        record["value"] = float(m["TravelTime"]["Time"]["content"])
        record["lane"] = "all"
        record["VehicleCategory"] = "all"
        trend_symbol = str(m["TravelTime"]["Trend"])
        if trend_symbol == '+':
            trend = 'rising'
        elif trend_symbol == '-':
            trend = 'falling'
        elif trend_symbol == '=':
            trend = 'steady'
        else:
            trend = trend_symbol
        record["trend"] = trend
        loc = {
                "type" : "Point",
                "coordinates" : [float(longi), float(lati)]
            } 
        record["loc"] = loc
        dt = datetime.now()
        gmt_dt = gmt.localize(dt)
        record["insertion_datetime"] = gmt_dt
        anprrecords.append(record)
        #AverageSpeed
        record = {}
        record["type"] = "AverageSpeed"
        record["typeSensor"] = "ANPR"
        record["measurement_id"] = str(m["SCN"])
        record["description"] = str(m["Description"])
        record["status"] = None
        (longi,lati) = ENtoLL.ENtoLL84(float(m["Easting"]), float(m["Northing"]))
        record["measurement_datetime"] = datetime.strptime(m["LastUpdated"], '%Y-%m-%d %H:%M:%S')
        record["value"] = float(m["AverageSpeed"]["Speed"]["content"])
        record["lane"] = "all"
        record["VehicleCategory"] = "all"
        trend_symbol = str(m["AverageSpeed"]["Trend"])
        if trend_symbol == '+':
            trend = 'rising'
        elif trend_symbol == '-':
            trend = 'falling'
        elif trend_symbol == '=':
            trend = 'steady'
        else:
            trend = trend_symbol
        record["trend"] = trend
        loc = {
                "type" : "Point",
                "coordinates" : [float(longi), float(lati)]
            } 
        record["loc"] = loc
        dt = datetime.now()
        gmt_dt = gmt.localize(dt)
        record["insertion_datetime"] = gmt_dt
        anprrecords.append(record)
    
    except Exception, e:
        print(e)
        sys.exit()
    
    return anprrecords
        
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


def push_data_to_local_collections():
    try:
        collections = get_collections_names_local("BCC_traffic")
    except Exception, e:
		print(e)
		sys.exit()
    try:
        new = False
        bcc_collections = ["Flows", "AverageSpeeds", "TravelTimes", "Congestions", "Occupancies", "ANPR"]
        for collection in bcc_collections:
            if str(collection) not in collections:
                new = True
                refresh_bcc_collections_local(str(collection))
    except Exception, e:
		print(e)
		sys.exit()
    try:
        if new:
            sys.exit()
        collections = get_collections_names_local("BCC_traffic")
    except Exception, e:
		print(e)
		sys.exit()
    try:
        for collection in collections:
            if str(collection) != 'system.indexes':
                col = establish_connection_local(str(collection))
                latest_readings = get_records_by_sensor_id_and_last_datetime(col)
                data = read_bcc_traffic(str(collection))
                records = process_bcc_traffic(str(collection),data,latest_readings)
                add_bcc_traffic_local(str(collection),records)
                
    except Exception, e:
		print(e)
		sys.exit()
            
if __name__ == '__main__':
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    push_data_to_local_collections()   #optimum vm mongoDB
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
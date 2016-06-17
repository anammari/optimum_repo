# -*- coding: utf-8 -*-
"""
Spyder Editor

Write the collection roadSensor for BCC to mongoDB on Intra Soft VM 
"""

import pymongo
from pymongo import InsertOne
import logging
from pytz import timezone
import datetime
import sys
import pandas as pd
from bson.son import SON

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')



def establish_connection_optimum(db_name, collection_name):
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

def fetch_sensor_info(input_collection, output_collection, sensorSource):
    gmt = timezone('GMT')
    try:
        endDt = datetime.datetime.now()
        gmt_e_date = gmt.localize(endDt)
        
        #start date is a month before the end date
        gmt_s_date = gmt_e_date - datetime.timedelta(days=30)
        
#        print startDt
#        print endDt
    except Exception, e:
    		print(e)
    		sys.exit()
    
    if sensorSource == 'BCC':
        logging.info("Started fetching 1 month of {} sensors".format(sensorSource))
        sensors = []
        types = ['AverageSpeed','Flow']
        typeSensor = ['ANPR','Detector','Scoot']
        try:
            pipeline = [
                  { "$match": { "insertion_datetime":     {"$gte": gmt_s_date,
                                                           "$lt": gmt_e_date},
                                'type' : { '$in' : types},
                                'typeSensor' : { '$in' : typeSensor} } },
                  { "$group": {
                                  "_id":{
                                  "loc": "$loc",
                                  "measurement_id" : "$measurement_id",
                                  "description" : "$description",
                                  "source" : "$typeSensor"
                                  },   
                  "total": { "$sum": 1 } 
                              }
                  },
                  {"$sort": SON([("total", -1)])}
            ]
            cursor = input_collection.aggregate(pipeline)
            
            for record in cursor:
                sensor = {}
                sensor['measurement_id'] = record['_id']['measurement_id']
                sensor['loc'] = record['_id']['loc']
                sensor['description'] = record['_id']['description']
                sensor['source'] = record['_id']['source']
                sensor['gmt_s_date'] = gmt_s_date
                sensor['gmt_e_date'] = gmt_e_date
                
                sensors.append(InsertOne(sensor))
                
            if len(sensors) > 0:
                #delete old sensor records in input collection
                query = {}
                cursor_count = output_collection.find(query).count()
                if cursor_count > 0:
                    logging.info("Found {} records in collection {} from {}".format(cursor_count,output_collection.name, sensorSource))
                    output_collection.remove(query)
                    logging.info("Deleted {} sensors from collection {}".format(sensorSource, output_collection.name))
                #store the sensors into the output collection
                result = output_collection.bulk_write(sensors)
                logging.info("Records added to collection {}: {}".format(output_collection.name,result.inserted_count))
        
                
        except Exception, e:
    		print(e)
    		sys.exit()

if __name__ == '__main__':
    output_collection = establish_connection_optimum("BccTraffic", "roadSensor")
    input_collection = establish_connection_optimum("BccTraffic", "roadSensorValue")
    fetch_sensor_info(input_collection, output_collection, "BCC")
    
    

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
import csv

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


def today():
    i = datetime.datetime.now()
    day = str(i.day)
    if len(day) == 1: day = '0' + day
    month = str(i.month)
    if len(month) == 1: month = '0' + month
    today = ("%s%s%s_" % (i.year, month, day))
    return today


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

def fetch_sensor_info(input_collection, sensorSource):
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
        types = ['AverageSpeed','Flow']
        typeSensor = ['Detector']
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
            logging.info("Finihsed fetching 1 month of {} sensors".format(sensorSource))
            logging.info("Started writing the CSV")
            f = open(today()+"sensors.csv", "wb")
            lines = []
            directions = ['I/B','O/B','E/B','W/B','S/B','N/B','ACW','CW']
            for record in cursor:
                direction = ''
                measurement_id = record['_id']['measurement_id'].encode("utf-8")
                lon = record['_id']['loc']['coordinates'][0]
                lat = record['_id']['loc']['coordinates'][1]
                description = record['_id']['description'].encode("utf-8")
                source = record['_id']['source']
                for d in directions:
                    if d in description:
                        direction = d
                        break
                    else:
                        continue
                line = '{},{},{},{},{},{}'.format(measurement_id,lon,lat,source,direction,description)
                    
                lines.append(line)
            w = csv.writer(f, delimiter = ',')
            w.writerows([x.split(',') for x in lines])
            f.close()
            logging.info("Finished writing the CSV")
                
        except Exception, e:
    		print(e)
    		sys.exit()

if __name__ == '__main__':
    input_collection = establish_connection_optimum("BccTraffic", "roadSensorValue")
    fetch_sensor_info(input_collection, "BCC")


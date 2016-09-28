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

def get_column_data(filename, cols):
    filtered_column_data = []
    csv_file = filename
    df = pd.read_csv(csv_file, header=None, dtype=object)
    saved_col = df.ix[:,cols]
    column_data = saved_col.tolist()
    for c in column_data:
        if str(c) != 'nan':
            filtered_column_data.append(str(c))
    return filtered_column_data
    
def fetch_sensor_info(filename, input_collection, output_collection, sensorSource):
    traffic_ids = get_column_data(filename,1)
#    print traffic_ids[0:10]
#    print str(len(traffic_ids))
    street_names = get_column_data(filename,2)
#    print street_names[0:10]
#    print str(len(street_names))
    way_ids = get_column_data(filename,3)
#    print way_ids[0:10]
#    print str(len(way_ids))
    directions = get_column_data(filename,4)
#    print directions[0:10]
#    print str(len(directions))
    
    sensors_streets = {}
    sensors_ways = {}
    sensors_directions = {}    
    
    for i in range(1,len(traffic_ids)):
        sensors_streets[traffic_ids[i]] = street_names[i]
        sensors_ways[traffic_ids[i]] = way_ids[i]
        sensors_directions[traffic_ids[i]] = directions[i]
        
    
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
        logging.info("Started fetching {} sensors".format(sensorSource))
        sensors = []
        types = ['AverageSpeed','Flow']
#        typeSensor = ['ANPR','Detector','Scoot']
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
            logging.info("Finihsed fetching {} sensors".format(sensorSource))
            
            for record in cursor:
                sensor = {}
                mId = record['_id']['measurement_id']
                sensor['measurement_id'] = mId
                sensor['loc'] = record['_id']['loc']
                sensor['description'] = record['_id']['description']
                sensor['source'] = record['_id']['source']
                sensor['gmt_s_date'] = gmt_s_date
                sensor['gmt_e_date'] = gmt_e_date
                
                if mId in sensors_streets.keys():
                    street_name = sensors_streets[mId]
                    if street_name != "NAN":
                        sensor['street_name'] = street_name
                    else:
                        sensor['street_name'] = ''
                else:
                    sensor['street_name'] = ''
                
                if mId in sensors_ways.keys():
                    way_id = sensors_ways[mId]
                    if way_id != "NAN":
                        if '-' in way_id:
                            sensor['way_id'] = way_id.split("-")[0]
                        else:
                            sensor['way_id'] = way_id
                    else:
                        sensor['way_id'] = ''
                else:
                    sensor['way_id'] = ''
                
                if mId in sensors_directions.keys():
                    direction = sensors_directions[mId]
                    if direction != "NAN":
                        sensor['direction'] = direction
                    else:
                        sensor['direction'] = ''
                else:
                    sensor['direction'] = ''
                
                sensors.append(InsertOne(sensor))
                
            if len(sensors) > 0:
                #delete old sensor records in input collection
                query = {"source" : "Detector"}
                cursor_count = output_collection.find(query).count()
                if cursor_count > 0:
                    logging.info("Found {} records in collection {} from {}".format(cursor_count,output_collection.name, sensorSource))
                    output_collection.remove(query)
                    logging.info("Deleted {} sensors from collection {}".format(sensorSource, output_collection.name))
                else:
                    logging.info("Found {} records in collection {} from {}".format(cursor_count,output_collection.name, sensorSource))
                #store the sensors into the output collection
                result = output_collection.bulk_write(sensors)
                logging.info("Records added to collection {}: {}".format(output_collection.name,result.inserted_count))
        
                
        except Exception, e:
    		print(e)
    		sys.exit()

if __name__ == '__main__':
    output_collection = establish_connection_optimum("BccTraffic", "roadSensor")
    input_collection = establish_connection_optimum("BccTraffic", "roadSensorValue")
    filename = "detector_sensors_osm_info.csv"
    fetch_sensor_info(filename, input_collection, output_collection, "BCC")
    
    

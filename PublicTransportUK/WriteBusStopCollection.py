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
#        host = "optimum.euprojects.net"
#        port = 3368
        host = "192.168.3.50"
        port = 27017
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
        if str(c) == 'nan':
            filtered_column_data.append('')
        else:
            filtered_column_data.append(str(c))
    return filtered_column_data
    
def write_bus_stop_info(filename, output_collection):
    try:
        atco_codes = get_column_data(filename,0)
#        print atco_codes[0:10]
#        print str(len(atco_codes))
        lons = get_column_data(filename,3)
        lats = get_column_data(filename,4)
        commonNames = get_column_data(filename,5)
        identifiers = get_column_data(filename,6)
        directions = get_column_data(filename,7)
        streets = get_column_data(filename,8)
        natGazIDs = get_column_data(filename,10)
        natGazLocalities = get_column_data(filename,11)
        stopTypes = get_column_data(filename,12)
        icon_colours = get_column_data(filename,14)
    
    except Exception, e:
		print(e)
		sys.exit()
    busStops = []    
    try:
        for i in range(1,len(atco_codes)):
            record = {}
            record[atco_codes[0]] = atco_codes[i]
            record[commonNames[0]] = commonNames[i]
            record[identifiers[0]] = identifiers[i]
            record[directions[0]] = directions[i]
            record[streets[0]] = streets[i]
            record[natGazIDs[0]] = natGazIDs[i]
            record[natGazLocalities[0]] = natGazLocalities[i]
            record[stopTypes[0]] = stopTypes[i]
            record[icon_colours[0]] = icon_colours[i]
            loc = {
                "type" : "Point",
                "coordinates" : [float(lons[i]), float(lats[i])]
            }            
            record["loc"] = loc
            
            busStops.append(InsertOne(record))
    except Exception, e:
		print(e)
		sys.exit()
  
    try:
        
        if len(busStops) > 0:
            #delete old records in input collection
            query = {}
            cursor_count = output_collection.find(query).count()
            if cursor_count > 0:
                logging.info("Found {} records in collection {}".format(cursor_count,output_collection.name))
                output_collection.remove(query)
                cursor_count_after_remove = output_collection.find(query).count()
                final_records_removed = cursor_count - cursor_count_after_remove
                logging.info("Deleted {} records from collection {}".format(final_records_removed, output_collection.name))
            else:
                logging.info("Found {} records in collection {}".format(cursor_count,output_collection.name))
            #store the sensors into the output collection
            result = output_collection.bulk_write(busStops)
            logging.info("Records added to collection {}: {}".format(output_collection.name,result.inserted_count))
    except Exception, e:
		print(e)
		sys.exit()

if __name__ == '__main__':
    output_collection = establish_connection_optimum("PublicTransportUK", "busStopsBirm")
    filename = "Bus_Coach_Stops_Birmingham.csv"
    write_bus_stop_info(filename, output_collection)
    
    

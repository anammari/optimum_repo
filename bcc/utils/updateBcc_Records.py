# -*- coding: utf-8 -*-
"""
Created on Thu Feb 28 2016

@author: Ahmad

Objectives: 
    - Update existing BCC Traffic records in 6 traffic-related collections 
    - Loop over the records in the given collection and update the record to the modified JSON structure
"""

import pymongo
import logging
from datetime import datetime
import sys

#logfile = 'C:\\Users\\Ahmad\\Dropbox\\Work\\Optimum\\bcc\\utils\\bcc_streams.log' #Windows local laptop
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

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

def loop_and_replace_docs(collection, collection_str):
    try:
        total_records_for_update = int(collection.find({"coordinates":{"$exists":True}}).count())
        log_message = str(total_records_for_update) + " records to be updated in " + collection_str
        logging.info(log_message)
        if total_records_for_update == 0:
            log_message = "All records are updated in " + collection_str
            return
        updated_recs = 0
        for record in collection.find(filter = {"coordinates":{"$exists":True}}):
            #Replace existing document with updated document 
            record2 = {}
            record2['_id'] = record['_id']
            record2["type"] = record["type"]
            record2["typeSensor"] = None
            record2["measurement_id"] = record["measurement_id"]
            record2["description"] = record["description"] 
            record2["status"] = record["status"]
            record2["measurement_datetime"] = record["measurement_datetime"]
            record2["value"] = record["value"]
            record2["lane"] = record["lane"]
            record2["VehicleCategory"] = record["VehicleCategory"]
            record2["trend"] = record["trend"]
            loc = {
                "type" : "Point",
                "coordinates" : [record["longitude"], record["latitude"]]
            }            
            record2["loc"] = loc
            record2["insertion_datetime"] = record["insertion_datetime"]
            
            collection.replace_one({'_id': record["_id"]},record2)
            
            updated_recs = updated_recs + 1
            
            if updated_recs == total_records_for_update:
                log_message = "Finished updating all records in " + collection_str
                logging.info(log_message)
                break
            if updated_recs % 1000 == 0:
                log_message = str(updated_recs) + " records updated in " + collection_str
                logging.info(log_message)
                    
    except Exception, e:
		print(e)
		sys.exit()
    

def update_data_in_local_collections():
    try:
        collections = get_collections_names_local("BCC_traffic")
    except Exception, e:
		print(e)
		sys.exit()
    try:
        bcc_collections = ["Flows", "AverageSpeeds", "TravelTimes", "Congestions", "Occupancies", "ANPR"]
        for collection in collections:
            if str(collection) not in bcc_collections:
                continue
            else:
                col = establish_connection_local(str(collection))
                loop_and_replace_docs(col, str(collection))
            
    except Exception, e:
		print(e)
		sys.exit()
    
            
if __name__ == '__main__':
    start = datetime.now() 
    update_data_in_local_collections()
    end = datetime.now()
    msg = "total execution time (sec): %s" % ((end-start).total_seconds())
    print msg







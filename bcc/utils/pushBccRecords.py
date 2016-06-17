# -*- coding: utf-8 -*-
"""
Created on Thu Mar 02 2016

Created on Thu Mar 03 2016

@author: Ahmad

Objectives: 
    - Push existing BCC Traffic records on UoW server datastore in 5 traffic-related collections 
        to Optimum VM server mongoDB 
    - The pushed records should be fetched from the source datastore based on a time window: 
        - Start datetime: 5 minutes before the last insertion datetime on the destination.
        - End datetime: 5 minutes before the last insertion datetime on the source.  
    - The script should run as a cronjob every 30 minutes on the UoW server (Windows OS).
"""

import pymongo
from pymongo import ReplaceOne
import logging
import datetime
import sys
from bson.json_util import dumps
from bson import json_util

logfile = 'C:\\Users\\Optimum\\Documents\\bcc\\bcc_push.log' #UoW Windows server
logging.basicConfig(filename=logfile, level=logging.INFO, format='%(asctime)s %(message)s')

def establish_connection_local(collection_name):
    try:
        # establish a connection to the collection
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

def establish_connection_optimum(collection_name):
    try:
        # establish a connection to the collection
        host = "euprojects.net"
        port = 3368
        db = 'BccTraffic'
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

def insert_new_records(input_collection, output_collection, collection_str):
    try:
        #get the last insertion time in the input collection
        last_inserted_doc_input = input_collection.find({}).sort('insertion_datetime', pymongo.DESCENDING).limit(1)
        last_insertion_time_input = last_inserted_doc_input[0]['insertion_datetime']
        #log last insertion time        
        log_message = "Last insertion datetime in " + collection_str + ": " + str(last_insertion_time_input)
        logging.info(log_message)
        #print for testing
#        print dumps(last_inserted_doc[0], indent=2, default=json_util.default)        
        
         #get the last insertion time in the output collection
        if "ies" not in collection_str:
            m_type = str(collection_str[:-1])
        else:
            m_type = str(collection_str[:-3]+"y")        
        
        last_inserted_doc_output = output_collection.find({"type" : m_type}).sort('insertion_datetime', pymongo.DESCENDING).limit(1)
        last_insertion_time_output = last_inserted_doc_output[0]['insertion_datetime']
        #log last insertion time        
        log_message = "Last insertion datetime in roadSensorValue for type " + m_type + ": " + str(last_insertion_time_output)
        logging.info(log_message)
        
        #get the datetime window
        end_date_time = last_insertion_time_input - datetime.timedelta(minutes = 5)
        start_date_time = last_insertion_time_output - datetime.timedelta(minutes = 5)
#        print for testing
#        print collection_str
#        print str(last_insertion_time_input)
#        print str(last_insertion_time_output)
#        print str(start_date_time)
#        print str(end_date_time)
#        print '***************************'
        
        #retrieve the records within the time window from the input collection
        query = {'insertion_datetime':{'$gte':start_date_time,'$lte':end_date_time}}
        cursor_count = int(input_collection.find(query).count())
        log_message = str(cursor_count) + " records to be inserted from " + collection_str
        logging.info(log_message)
        cursor = input_collection.find(query)
        
        #bulk write to the output collection
        requests = []
        for doc in cursor:
            requests.append(ReplaceOne({ "_id" : doc["_id"] }, doc, upsert=True))
        
        #write the new records to the output collection        
        result = output_collection.bulk_write(requests)
        
        #log counts
        log_message = str(result.upserted_count) + " records were upserted from " + collection_str + " to roadSensorValue"
        logging.info(log_message)
        log_message = str(result.matched_count) + " records were matched in roadSensorValue"
        logging.info(log_message)


    except Exception, e:
		print(e)
		sys.exit()
    

def push_bcc_traffic_data_to_optimum_db():
    try:
        collections = get_collections_names_local("BCC_traffic")
    except Exception, e:
		print(e)
		sys.exit()
    try:
        bcc_collections = ["Flows", "AverageSpeeds", "TravelTimes", "Congestions", "Occupancies"]
        for collection in collections:
            if str(collection) not in bcc_collections:
                continue
            else:
                input_col = establish_connection_local(str(collection))
                output_col = establish_connection_optimum(str("roadSensorValue"))
                insert_new_records(input_col, output_col, str(collection))
            
    except Exception, e:
		print(e)
		sys.exit()
    
            
if __name__ == '__main__':
    start = datetime.datetime.now() 
    push_bcc_traffic_data_to_optimum_db()
    end = datetime.datetime.now()
    msg = "total execution time (sec): %s" % ((end-start).total_seconds())
    logging.info(msg)







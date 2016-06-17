# -*- coding: utf-8 -*-
"""
Spyder Editor

Generates hourly aggregates of the extracted Highway mentions from traffic informing tweets

"""

import datetime
import sys
from pytz import timezone
from bson import json_util
from bson.json_util import dumps
import pymongo
from pymongo import InsertOne
from bson.son import SON
import logging
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

def establish_connection_optimum(collection_name):
    try:
        # establish a connection to the collection
        host = "192.168.3.50"
        port = 27017
        db = 'Twitter'
        user = ''
        password = ''
        collection = collection_name
        connection = pymongo.MongoClient(host, port)
#        connection[db].authenticate(user, password)
        return connection[db][collection]
    
    except Exception, e:
        print(e)
        sys.exit()

def fetch_hr_aggregates(threadName,ner_collection,output_collection,gmt_s_date,gmt_e_date,source):
    #if there are aggregates in the output collection for the date, remove them
    try:
        query = {"gmt_date":{'$gte':gmt_s_date,'$lt':gmt_e_date}}
        num_aggs_output = output_collection.find(query).count()
        
        if num_aggs_output > 0:
            log_message = "{}: No of aggregates found from the thread date in collection {}: {} ... Deleting them ...".format(threadName,output_collection.name,str(num_aggs_output))
            logging.info(log_message)
            output_collection.remove(query)
            num_aggs_output = output_collection.find(query).count()
            log_message = "{}: No of aggregates found from the thread date in collection {}: {}".format(threadName,output_collection.name,str(num_aggs_output))
        else:
            logging.info("{}: No aggregates found from the thread date in collection {}".format(threadName,output_collection.name))
    except Exception, e:
        print(e)
        sys.exit()
    
    log_message = "{}: Started hourly aggregations for the thread date".format(threadName)
    logging.info(log_message)
    try:
        pipeline = [
              { "$match": { "gmt_tweet_date":     {"$gte": gmt_s_date,
                                                   "$lt": gmt_e_date}
              } },
              { "$group": {
              "_id":{
              "ner_id": "$highway_code",
              "ner_date": {
                "year": { "$year": "$gmt_tweet_date"},
                "month": { "$month": "$gmt_tweet_date" },
                "day": { "$dayOfMonth": "$gmt_tweet_date" },
                "hour": { "$hour": "$gmt_tweet_date" }
                   }
              },   
              "total": { "$sum": 1 } 
              }
              },
              {"$sort": SON([("_id.ner_date.year", 1), ("_id.ner_date.month", 1), ("_id.ner_date.day", 1),
                             ("_id.ner_date.hour", 1), ("total", -1)])}
        ]
        cursor = ner_collection.aggregate(pipeline)
    except Exception, e:
		print(e)
		sys.exit()
    log_message = "{}: Started writing hourly aggregations for the thread date to collection {}".format(threadName,output_collection.name)
    logging.info(log_message)
    #Print for testing
#    print dumps(cursor, indent=2, default=json_util.default)
    write_mongo(threadName,cursor,output_collection,source)
    log_message = "{}: Finished writing hourly aggregations for the thread date to collection {}".format(threadName,output_collection.name)
    logging.info(log_message)

def write_mongo(threadName,cursor,output_collection,source):
    gmt = timezone('GMT')
    try:
        hr_aggregates = []
        for record in cursor:
            doc = {}
            value = record["total"]
            highway_code = record["_id"]["ner_id"].encode("utf-8")
            year = str(record["_id"]["ner_date"]["year"])
            month = str(record["_id"]["ner_date"]["month"])
            month = month.zfill(2)
            day = str(record["_id"]["ner_date"]["day"])
            day = day.zfill(2)
            hour = str(record["_id"]["ner_date"]["hour"])
            hour = hour.zfill(2)
            agg_date = datetime.datetime.strptime(day+'-'+month+'-'+year+' '+hour+':00:00', '%d-%m-%Y %H:%M:%S')
            gmt_date = gmt.localize(agg_date)
            
            doc['highway_code'] = highway_code
            doc['value'] = value
            doc['gmt_date'] = gmt_date
            doc['source'] = source
            
            hr_aggregates.append(InsertOne(doc))
            
        if len(hr_aggregates) > 0:        
            #write the new records to the output collection        
            result = output_collection.bulk_write(hr_aggregates)
            logging.info("{}: Records added to mongoDB: {}".format(threadName,result.inserted_count))
        else:
            logging.info("{}: Records added to mongoDB: {}".format(threadName,len(hr_aggregates)))
            
    except Exception, e:
		print(e)
		sys.exit()
  
def process_days(threadName,ner_collection,output_collection,next_date,end_date,source):
    try:
        logging.info("{}: Started hourly aggregations for date: {}".format(threadName,next_date.strftime('%a %b %d %Y')))
        fetch_hr_aggregates(threadName,ner_collection,output_collection,next_date,end_date,source)
        logging.info("{}: Finished fetching hourly aggregates ...".format(threadName))
            
    except Exception, e:
        print(e)
        sys.exit()

def parallel_process_days(start_date_str,end_date_str,source):
    gmt = timezone('GMT')
    try:
        ner_collection = establish_connection_optimum("uk_accounts_highway_mentions")
        output_collection = establish_connection_optimum("uk_accounts_highway_hr_agg")
        logging.info("DB connecttion established ...")
    except Exception, e:
        print(e)
        sys.exit()
    try:
        startDt = datetime.datetime.strptime(start_date_str+' 00:00:00 +0000 2016', '%a %b %d %H:%M:%S +0000 %Y')
        endDt =  datetime.datetime.strptime(end_date_str+' 00:00:00 +0000 2016', '%a %b %d %H:%M:%S +0000 %Y')
        gmt_s_date = gmt.localize(startDt)
        gmt_e_date = gmt.localize(endDt)
        next_date = gmt_s_date
    except Exception, e:
        print(e)
        sys.exit()
         
    try:
        while next_date < gmt_e_date:
            end_date = next_date + datetime.timedelta(days=1)
            t = threading.Thread(target=process_days, args=("Thread-{}".format(next_date.strftime('%a-%b-%d-%Y')), 
                                                    ner_collection, output_collection, next_date, end_date, source))
            t.start()            
            next_date += datetime.timedelta(days=1)
        
    except Exception, e:
        print(e)
        sys.exit()
        
if __name__ == '__main__':
    start_date_str = 'Sat Mar 12'
    end_date_str = 'Thu Mar 24'
    source = "UKTraffic"
    parallel_process_days(start_date_str,end_date_str,source)
    logging.info("All Done!")

# -*- coding: utf-8 -*-
"""
Spyder Editor

Write Twitter corpos classified using SentiWordNet, RapidMiner, and R into mongoDB collection for training
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
        if str(c) != 'nan':
            filtered_column_data.append(str(c))
    return filtered_column_data

def read_senti_tweets(filename,output_collection):
    
        logging.info("Started reading senti tweets from text file")
        sentiTweets = []
        try:
            tweetTexts = get_column_data(filename,0)
            tweetClasses = get_column_data(filename,1)
            logging.info("Finished reading senti tweets from text file")
#            print str(len(tweetTexts))
#            for i in range(0,5):
#                print tweetTexts[i]
#            print tweetTexts[1:5]
#            print str(len(tweetClasses))
#            print tweetClasses[1:5]
            
            if len(tweetTexts) == len(tweetClasses) and len(tweetTexts) > 2:
                
                logging.info("Started writing {} senti tweets to collection {}".format(len(tweetTexts),output_collection.name))           
                for i in range(1,len(tweetTexts)):
                    sentiTweet = {}
                    sentiTweet['text'] = tweetTexts[i]
                    sentiTweet['label'] = tweetClasses[i]
                
                    sentiTweets.append(InsertOne(sentiTweet))
                    
                if len(sentiTweets) > 0:
                    #delete old sensor records in input collection
                    cursor_count = output_collection.find({}).count()
                    if cursor_count > 0:
                        logging.info("Found {} records in collection {}".format(cursor_count,output_collection.name))
                        output_collection.remove({})
                        logging.info("Deleted {} records from collection {}".format(cursor_count, output_collection.name))
                    #store the sensors into the output collection
                    result = output_collection.bulk_write(sentiTweets)
                    logging.info("Records added to collection {}: {}".format(output_collection.name,result.inserted_count))
#        
#                
        except Exception, e:
    		print(e)
    		sys.exit()
    

if __name__ == '__main__':
    output_collection = establish_connection_optimum("Twitter", "SentiTrainingTweets")
    filename = "df_tweets_for_training.csv"
    sentiTweets = read_senti_tweets(filename,output_collection)
    
    

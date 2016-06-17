#!/usr/local/lib/python2.7.11/bin/python

"""
Created on Tue Mar 08 2016
Modified on Fri Mar 11 2016

@author: Ahmad

Objectives: 
    - Stream accounts coming from the United Kingdom
    - Steam key words related to traffic
    - Add attributes that contain the ISO Dates for the tweets and the original quoted tweets' 
    - Write each streamed tweet to mongoDB (Intrasoft VM)
"""

import csv
from tweepy.streaming import StreamListener
from pytz import timezone
from tweepy import OAuthHandler
from tweepy import Stream
from time import gmtime, strftime
import datetime
import json
import logging
import numpy
from HTMLParser import HTMLParser
import pymongo
import sys
from httplib import IncompleteRead

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

def establish_connection_local(collection_name):
    try:
        # establish a connection to the collection
        host = 'localhost'
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

def readTwitterTrafficAccounts(filename):
    try:
        with open(filename, 'rb') as f:
            reader = csv.reader(f)
            your_list = list(reader)
        final_list = [item for sublist in your_list for item in sublist]
        return final_list
    
    except Exception, e:
        print(e)
        sys.exit()

def readTwitterTrafficKeywords(filename):
    try:
        with open(filename, 'rb') as f:
            reader = csv.reader(f)
            your_list = list(reader)
        final_list = [item for sublist in your_list for item in sublist]
        final_list = final_list[1:]
        final_list = list(set(final_list))
        return final_list
    
    except Exception, e:
        print(e)
        sys.exit()

# Twitter Account: @EuOptimumSocial
# App name: Optimum_UK_Streams
# App URL: https://apps.twitter.com/app/12015808
consumer_key="gY9itNhl24sWkvePBaS6qljbY"
consumer_secret="I58RHxUdB7cI8LG9Z0BZE045nVJWbrEaTPivIjKxOh8PrIVKAZ"

# After the step above, you will be redirected to your app's page.
# Create an access token under the the "Your access token" section
access_token="702806431154708480-miRWDv5VVoqprkrHFnbMYEGAjIsNy3W"
access_token_secret="jQ7DHr7oOYM0fYrBoFhMrqlNEqKBTLMtwenlNtnGFu1fA"

# logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

#On Intrasoft's VM
logging.basicConfig(filename='/home/optimum/optimum_uk_accounts/twitter_streaming/logs/uk_accounts.log',
                    level=logging.INFO, format='%(asctime)s %(message)s')

#Collection handle to use for inserting tweets to mongoDB collection
collection = None

class StdOutListener(StreamListener):
    """ A listener handles tweets are the received from the stream.
    This is a basic listener that just prints received tweets to stdout.
    """

    def __init__(self, api=None):
        super(StdOutListener, self).__init__()
        self.num_tweets = 0
        self.error_message = ""

        # get a handle to the collection
        self.stream = collection

    def on_data(self, data):

        try:
            decoded = json.loads(data)
            decoded['text'] = decoded['text'].encode('utf-8', 'ignore')
            created_at = datetime.datetime.strptime(decoded['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
            gmt = timezone('GMT')
            gmt_tweet_date = gmt.localize(created_at)
            decoded['gmt_tweet_date'] = gmt_tweet_date
            if "retweeted_status" in decoded.keys():
                try:
                    created_at = datetime.datetime.strptime(decoded['retweeted_status']['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
                    original_gmt_tweet_date = gmt.localize(created_at)
                    decoded['retweeted_status']['gmt_tweet_date'] = original_gmt_tweet_date
                
                except Exception, e:
                    pass
                
            if "quoted_status" in decoded.keys():
                try:
                    created_at = datetime.datetime.strptime(decoded['quoted_status']['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
                    original_gmt_tweet_date = gmt.localize(created_at)
                    decoded['quoted_status']['gmt_tweet_date'] = original_gmt_tweet_date

                except Exception, e:
                    pass

        except KeyError as e:
            logging.error(e.message)
            return True

        except ValueError as e:
            logging.error(e.message)
            return True

        except AttributeError as e:
            logging.error(e.message)
            return True

        except:
            self.error_message = sys.exc_info()[0]
            logging.error(self.error_message)
            return True

        try:

            self.stream.insert(decoded)
#            print decoded 

            self.num_tweets = int(self.stream.find().count())
#            
            if self.num_tweets != 0 and self.num_tweets % 1000 == 0:
                log_message = str(self.num_tweets) + " tweets"
                logging.info(log_message)

            return True

        except Exception, e:
            self.error_message = sys.exc_info()[0]
            logging.error(self.error_message)
#            print e.message
            return True


    def on_error(self, status):
        logging.error(status)
        return True
    
    def on_delete(self, status_id, user_id):
        """Called when a delete notice arrives for a status"""
        msg = "Delete notice for %s. %s" % (status_id, user_id)
        logging.error(msg)
        return True
        
    def on_limit(self, track):
        """Called when a limitation notice arrvies"""
        msg = "!!! Limitation notice received: %s" % str(track)
        logging.error(msg)
        return True
        
    def on_timeout(self):
        msg = '%s: Timeout...' % (sys.stderr)
        logging.error(msg)
        return True

if __name__ == '__main__':
    starting_message = "Started streaming UK accounts and keywords"
    logging.info(starting_message)
#     collection = establish_connection_local("uk_accounts")  #Testing on Macbook local machine
    collection = establish_connection_optimum("uk_accounts")
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    
    accounts = readTwitterTrafficAccounts("/home/optimum/optimum_uk_accounts/twitter_streaming/TwitterTrafficAccounts.csv")
#     accounts = readTwitterTrafficAccounts("TwitterTrafficAccounts.csv")
    accounts = accounts[1:]
    
    keywords = readTwitterTrafficKeywords("/home/optimum/optimum_uk_accounts/twitter_streaming/TwitterTrafficPhrases.csv")
#     keywords = readTwitterTrafficKeywords("TwitterTrafficPhrases.csv")
    
    while True:
        try:
            stream = Stream(auth, l, timeout= 300)
            stream.filter(languages=["en"], track=keywords, follow=accounts)
        except (AttributeError, IncompleteRead) as e:
            logging.error(e)
            continue

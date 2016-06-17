#!/usr/local/lib/python2.7.11/bin/python

"""
Created on Fri Jun 11 2016

@author: Ahmad

Objectives: 
    - Stream tweets coming from Slovenia
    - Add attributes that contain the ISO Dates for the tweets and the original quoted tweets 
    - Write each streamed tweet to mongoDB (Intrasoft VM)
"""

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
#        host = "optimum.euprojects.net"
#        port = 3368
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


# Twitter Account: @EuOptimumSocial
# App name: Optimum_SL_Streams
# App URL: https://apps.twitter.com/app/12476644
consumer_key="Gh5P6m4rHhETNcbgYHM357Eoo"
consumer_secret="cXTU6bXMYoHqjKLoeNwVV6fiZ0wETe8kT0A1cltMBZqQmrmIzH"

# After the step above, you will be redirected to your app's page.
# Create an access token under the the "Your access token" section
access_token="702806431154708480-cMIt7RYjWhn3TCcwZBv4jNrsDrbZzqR"
access_token_secret="YEPl2GTqmideBtCtX3QV9jbRXEYCN8jaRxDwyQQgWTwh7"

#logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

#On Intrasoft's VM
logging.basicConfig(filename='/home/optimum/optimum_sl_streams/twitter_streaming/logs/sl_tweets.log',
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
            decoded['tweet_date'] = gmt_tweet_date
            if "retweeted_status" in decoded.keys():
                try:
                    created_at = datetime.datetime.strptime(decoded['retweeted_status']['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
                    original_gmt_tweet_date = gmt.localize(created_at)
                    decoded['retweeted_status']['tweet_date'] = original_gmt_tweet_date
                
                except Exception, e:
                    pass
                
            if "quoted_status" in decoded.keys():
                try:
                    created_at = datetime.datetime.strptime(decoded['quoted_status']['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
                    original_gmt_tweet_date = gmt.localize(created_at)
                    decoded['quoted_status']['tweet_date'] = original_gmt_tweet_date

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
#            print decoded['text'] 

            self.num_tweets = int(self.stream.find().count())
#            
            if self.num_tweets != 0 and self.num_tweets % 500 == 0:
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
    starting_message = "Started streaming Slovenia tweets"
    logging.info(starting_message)
#     collection = establish_connection_local("sl_tweets")  #Testing on Macbook local machine
    collection = establish_connection_optimum("sl_tweets")
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    
    while True:
        try:
            stream = Stream(auth, l, timeout= 300)
            stream.filter(locations=[13.3755, 45.4160, 16.5966, 46.8779])
        except IncompleteRead, e:
            logging.error(e)
            continue

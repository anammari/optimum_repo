# -*- coding: utf-8 -*-
"""
Spyder Editor

Extraction of Traffic Concept and Term Mentions from traffic-informing tweets
"""

import pymongo
from pymongo import InsertOne
import logging
import datetime
import re
import string
from nltk.corpus import stopwords
from pytz import timezone
import sys
import threading

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

#Utility functions for text preprocessing
emoticons_str = r"""
    (?:
        [:=;] # Eyes
        [oO\-]? # Nose (optional)
        [D\)\]\(\]/\\OpP] # Mouth
    )"""

regex_str = [
    emoticons_str,
    r'<[^>]+>', # HTML tags
    r'(?:@[\w_]+)', # @-mentions
    r"(?:\#+[\w_]+[\w\'_\-]*[\w_]+)", # hash-tags
    r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+', # URLs

    r'(?:(?:\d+,?)+(?:\.?\d+)?)', # numbers
    r"(?:[a-z][a-z'\-_]+[a-z])", # words with - and '
    r'(?:[\w_]+)', # other words
    r'(?:\S)' # anything else
]

tokens_re = re.compile(r'('+'|'.join(regex_str)+')', re.VERBOSE | re.IGNORECASE)
emoticon_re = re.compile(r'^'+emoticons_str+'$', re.VERBOSE | re.IGNORECASE)

punctuation = list(string.punctuation)
stop = stopwords.words('english') + punctuation + ['rt', 'via', 'amp', 'retweet', 'please retweet', 'retweet please']

def tokenize(s):
    return tokens_re.findall(s)

def preprocess(s, lowercase=False):
    tokens = tokenize(s)
    if lowercase:
        tokens = [token if emoticon_re.search(token) else token.lower() for token in tokens]
    preprocessed_tokens = []
    for tok in tokens:
        if not bool(re.search(r'([.,:;\'"<>=/\\@!])',tok)):
            if bool(re.search(r'#',tok)):
                preprocessed_tokens.append(tok[1:])
            else:
                preprocessed_tokens.append(tok)
    return preprocessed_tokens

#Test the preprocessing functions
#tweet = "RT @marcobonzanini: delays #example of modern slavery #M44!!!! for #climate change! #B60 :D :-) http://example.com #NLP"
#print(preprocess(tweet))
#terms_all = [term for term in preprocess(tweet.lower()) if term not in stop]
#print terms_all
#text = " ".join(terms_all)
#search_element = "DELAYS"
#bool(re.search(r'(^|\s|[.,:;\'"<>=/\\#])'+search_element+r'($|\s|\W)',text, re.IGNORECASE))

def today():
    i = datetime.datetime.now()
    day = str(i.day)
    if len(day) == 1: day = '0' + day
    month = str(i.month)
    if len(month) == 1: month = '0' + month
    today = ("%s%s%s_" % (i.year, month, day))
    return today

def establish_connection_optimum(collection_name):
    try:
        # establish a connection to the collection
        host = "192.168.3.50"
        port = 27017
        db = "Twitter"
        user = ''
        password = ''
        collection = collection_name
        connection = pymongo.MongoClient(host, port)
#        connection[db].authenticate(user, password)
        return connection[db][collection]
    
    except Exception, e:
        print(e)
        sys.exit()

def fetch_tweets(threadName,stream,output_collection,gmt_s_date,gmt_e_date):
    fetchedTweets = []
    #decide on the gmt_s_date based on the last gmt_tweet_date stored in the output collection
    try:
        query = {"gmt_tweet_date":{'$gte':gmt_s_date,'$lt':gmt_e_date}}
        num_tweets_output = output_collection.find(query).count()
        if num_tweets_output > 0:
            last_tweet_output = output_collection.find(query).sort('gmt_tweet_date', pymongo.DESCENDING).limit(1)
            last_tweet_time_output = last_tweet_output[0]['gmt_tweet_date']
            #log last insertion time        
            log_message = "{}: Last tweet from the thread date in NER collection: {}".format(threadName,last_tweet_time_output)
            logging.info(log_message)
            gmt_s_date = last_tweet_time_output
        else:
            logging.info("{}: No tweets found from the thread date in NER collection".format(threadName))
    except Exception, e:
        print(e)
        sys.exit()    
    try:
        query = {"gmt_tweet_date":{'$gte':gmt_s_date,'$lt':gmt_e_date}}
        num_tweets = stream.find(query).count()
        logging.info("{}: No of tweets to be fetched: {} tweets".format(threadName, num_tweets))
        cursor = stream.find(query)
    except Exception, e:
        print(e)
        sys.exit()
    for doc in cursor:
        fetchedTweet = {}
        try:
            tweetId = doc['id']
            screen_name = doc['user']['screen_name']
            text = doc['text']
            gmt_tweet_date = doc['gmt_tweet_date']
        except KeyError, e:
            continue
        
        except Exception, e:
            print(e)
            sys.exit()
        
        fetchedTweet['tweetId'] = tweetId            
        fetchedTweet['screen_name'] = screen_name
        fetchedTweet['text'] = text
        fetchedTweet['gmt_tweet_date'] = gmt_tweet_date
        
        fetchedTweets.append(fetchedTweet)
        if len(fetchedTweets) % 1000 == 0:
            logging.info("{}: Tweets fetched: {} tweets".format(threadName, len(fetchedTweets)))
    return fetchedTweets
    
        
def preprocess_tweets(fetchedTweets):
    try:
        for fetchedTweet in fetchedTweets:
            text = fetchedTweet['text']
            terms_all = [term for term in preprocess(text) if term not in stop]
            sentence = " ".join(terms_all)
            sentence = sentence.upper()
            
            fetchedTweet['cleaned_text'] = sentence
            
    except Exception, e:
        print(e)
        sys.exit()
    
    return fetchedTweets

def extract_traffic_mentions(threadName,output_collection,fetchedTweets,traffic_gazetteer):
    try:
        counter = 0
        mongo_list = []
        for fetchedTweet in fetchedTweets:
            counter += 1
            traffic_tuples = []
            concepts = []
            sentence = fetchedTweet['cleaned_text']
            for traffic_tuple in traffic_gazetteer:
                if bool(re.search(r'(^|\s|[.,:;\'"<>=/\\#])'+traffic_tuple[1]+r'($|\s|\W)',sentence, re.IGNORECASE)):
                    if traffic_tuple[0] not in concepts:
                        traffic_tuples.append(traffic_tuple)
                        concepts.append(traffic_tuple[0])
                    else:
                        continue
                else:
                    continue
            fetchedTweet['traffic_tuples'] = traffic_tuples
            
            mongo_list.append(fetchedTweet)
            if counter % 100 == 0:
                logging.info("{}: Tweets processed: {} tweets".format(threadName, counter))
                write_mongo(threadName,output_collection,mongo_list)
                mongo_list = []
        if len(mongo_list) > 0:
            write_mongo(threadName,output_collection,mongo_list)
            mongo_list = []
    except Exception, e:
        print(e)
        sys.exit()

def write_mongo(threadName,output_collection,mongo_list):
    try:
        #bulk write to the output collection
        tweets = []
        for fetchedTweet in mongo_list:
            if len(fetchedTweet['traffic_tuples']) > 0:
                traffic_tuples = fetchedTweet['traffic_tuples']
                for tt in traffic_tuples:
                    doc = {}
                    doc['tweetId'] = fetchedTweet['tweetId']
                    doc['gmt_tweet_date'] = fetchedTweet['gmt_tweet_date']
                    doc['gmt_tweet_date_str'] = fetchedTweet['gmt_tweet_date'].strftime('%d/%m/%Y')
                    doc['gmt_tweet_hour'] = fetchedTweet['gmt_tweet_date'].strftime('%H')
                    doc['screen_name'] = fetchedTweet['screen_name']
                    doc['traffic_concept'] = tt[0]
                    doc['traffic_term'] = tt[1]
                    tweets.append(InsertOne(doc))
                    
            else:
                continue
        
        if len(tweets) > 0:
            #write the new records to the output collection        
            result = output_collection.bulk_write(tweets)
            logging.info("{}: Records added to mongoDB: {}".format(threadName,result.inserted_count))
        else:
            logging.info("{}: Records added to mongoDB: {}".format(threadName,len(tweets)))
    except Exception, e:
        print(e)
        sys.exit()

def process_days(threadName,stream,output_collection,traffic_gazetteer,next_date,end_date):
    try:
        logging.info("{}: Started fetching tweets for date: {}".format(threadName,next_date.strftime('%a %b %d %Y')))
        fetchedTweets = fetch_tweets(threadName,stream,output_collection,next_date,end_date)
        logging.info("{}: Finished fetching tweets ...".format(threadName))
        logging.info("{}: Started preprocessing tweets ...".format(threadName))
        preprocessedTweets = preprocess_tweets(fetchedTweets)
        logging.info("{}: Finished preprocessing tweets ...".format(threadName))
        logging.info("{}: Started extracting traffic mentions ...".format(threadName))
        extract_traffic_mentions(threadName,output_collection,preprocessedTweets,traffic_gazetteer)
        logging.info("{}: Finished extracting traffic mentions ...".format(threadName))
            
    except Exception, e:
        print(e)
        sys.exit()

def parallel_process_days(start_date_str,end_date_str):
    gmt = timezone('GMT')
    try:
        stream = establish_connection_optimum("uk_accounts")
        output_collection = establish_connection_optimum("uk_accounts_traffic_mentions")
        traffic_collection = establish_connection_optimum("TrafficGazetteer")
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
    #fetch the highway codes from db collection and store them in a list
    try:
        traffic_gazetteer = []
        query = {}
        num_records = traffic_collection.find(query).count()
        if num_records < 1:
            logging.info("No records found in collection {}. Exiting ...".format(num_records))
            sys.exit()
        cursor = traffic_collection.find(query)
        for doc in cursor:
            (concept,term) = (doc['Traffic_concept'].encode("utf-8"),doc['Traffic_term'].encode("utf-8"))
            traffic_gazetteer.append((concept,term))
        
    except Exception, e:
        print(e)
        sys.exit()
        
        
    try:
        while next_date < gmt_e_date:
            end_date = next_date + datetime.timedelta(days=1)
            t = threading.Thread(target=process_days, args=("Thread-{}".format(next_date.strftime('%a-%b-%d-%Y')), 
                                                    stream, output_collection, traffic_gazetteer, next_date, end_date, ))
            t.start()            
            next_date += datetime.timedelta(days=1)
        
    except Exception, e:
        print(e)
        sys.exit()
            

#Test Stanford NER Tagger
#neList = st.tag('Rami Eid is studying at Stony Brook University in New York'.split())
#for ne in neList:
#    if ne[1] in ['PERSON', 'ORGANIZATION', 'LOCATION']:
#        print ne[0] + ' is ' + ne[1]

if __name__ == '__main__':
    start_date_str = 'Sun May 01'
#    end_date_str = 'Fri Apr 01'
    end_date_str = 'Mon May 23'
    parallel_process_days(start_date_str,end_date_str)
    logging.info("All Done!")

# -*- coding: utf-8 -*-
"""
Spyder Editor

Classify traffic-informing tweets into positive, neutral, positive with class probability. Store in mongoDB
Version 2: This version takes advantage of the batch classification feature of sciket-learn
"""

from __future__ import division
try:
   import cPickle as pickle
except:
   import pickle
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn import svm
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
import os
import math
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

#Global variables
sentiment_classifier_filename = '/home/optimum/social_entity_extraction/TwitterSentimentsScikitLearnSVM/semtiment_classifier.pickle'
sentiment_vectorizer_filename = '/home/optimum/social_entity_extraction/TwitterSentimentsScikitLearnSVM/sentiment_vectorizer.pickle'
start_date_str = 'Tue Jun 28'
end_date_str = 'Wed Jun 29'
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

def save_classifier(classifier):
    global sentiment_classifier_filename
    f = open(sentiment_classifier_filename, 'wb')
    pickle.dump(classifier, f, -1)
    f.close()
    
def save_vectorizer(vectorizer):
    global sentiment_vectorizer_filename
    f = open(sentiment_vectorizer_filename, 'wb')
    pickle.dump(vectorizer, f, -1)
    f.close()

def load_classifier():
    global sentiment_classifier_filename
    f = open(sentiment_classifier_filename, 'rb')
    classifier = pickle.load(f)
    f.close()
    return classifier

def load_vectorizer():
    global sentiment_vectorizer_filename
    f = open(sentiment_vectorizer_filename, 'rb')
    vectorizer = pickle.load(f)
    f.close()
    return vectorizer

def train_senti_model(training_collection):
    global sentiment_classifier_filename
    global sentiment_vectorizer_filename
    if os.path.isfile(sentiment_classifier_filename) and os.path.isfile(sentiment_vectorizer_filename):
        logging.info("classifier/vectorizer found and will be loaded from files")
        return
    else:
        # Read the training data from mongo
        query = {}
        project = {"_id": 0, "text": 1, "label": 1}
        numTweets = training_collection.find(query).count()
        logging.info("Started reading {} training senti tweets".format(numTweets))
        train_data = []
        train_labels = []
        try:
            cursor = training_collection.find(query,project)
            for doc in cursor:
                train_data.append(doc['text'])
                train_labels.append(doc['label'])
        except Exception, e:
            print(e)
            sys.exit()
        
        logging.info("Finished reading training senti tweets")
        
        # Create feature vectors
        try:
            vc = TfidfVectorizer(min_df=5,
                                     max_df = 0.99,
                                     sublinear_tf=True,
                                     use_idf=True,
                                     decode_error='ignore')
            train_vectors = vc.fit_transform(train_data)
        except Exception, e:
            print(e)
            sys.exit()
            
        # Perform training with SVM, kernel=LinearSVC
        try:
            logging.info("Started training model")
            cl = svm.LinearSVC()
            t0 = time.time()
            cl.fit(train_vectors, train_labels)
            t1 = time.time()
            time_liblinear_train = t1-t0
            logging.info("Finished training. Training Time (sec): {}".format(time_liblinear_train))
        except Exception, e:
            print(e)
            sys.exit()
        
        # Persist the classifier / vectorizer
        save_classifier(cl)
        save_vectorizer(vc)

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

def classify_tweets_sentiments(threadName,output_collection,fetchedTweets):
    #Prepare the mongo lists for sentiment classification
    try:
        counter = 0
        mongo_list = []
        sentences = []
        for fetchedTweet in fetchedTweets:
            counter += 1
            sentence = fetchedTweet['cleaned_text']
            sentences.append(sentence)
            mongo_list.append(fetchedTweet)
            if counter % 1000 == 0:
                mongo_list_post = classify_mongo_list(mongo_list,sentences)
                write_mongo(threadName,output_collection,mongo_list_post)
                mongo_list = []
                sentences = []
            else:
                continue
        if len(mongo_list) > 0:
            mongo_list_post = classify_mongo_list(mongo_list,sentences)
            write_mongo(threadName,output_collection,mongo_list_post)
            mongo_list = []
            sentences = []
    except Exception, e:
        print(e)
        sys.exit()

def classify_mongo_list(mongo_list,sentences):
    mongo_list_post = []
    #Load the classifier / vectorizer 
    try:
        cl = load_classifier()
        vc = load_vectorizer()
    except Exception, e:
        print(e)
        sys.exit()
    
    #Classify each tweet in the mongo list and stores its sentiment class and probability
    try:
        vectorized_sentences = vc.transform(sentences)
        predictions = cl.predict(vectorized_sentences)
        decision_fn_np_output = cl.decision_function(vectorized_sentences)
        for i in range(0, len(mongo_list)):
            decision_fn_output = []
            fetchedTweet = mongo_list[i]
            fetchedTweet['sentiment_class'] = predictions[i]
            for x in np.nditer(decision_fn_np_output[i]):
                decision_fn_output.append(1 / (1 + math.exp(-1 * x)))
            fetchedTweet['class_probability'] = max(decision_fn_output)
            mongo_list_post.append(fetchedTweet)
    except Exception, e:
        print(e)
        sys.exit()
    
    return mongo_list_post
    
def write_mongo(threadName,output_collection,mongo_list):
    try:
        #bulk write to the output collection
        tweets = []
        if len(mongo_list) > 0:
            for fetchedTweet in mongo_list:
                doc = {}
                doc['tweetId'] = fetchedTweet['tweetId']
                doc['gmt_tweet_date'] = fetchedTweet['gmt_tweet_date']
                doc['gmt_tweet_date_str'] = fetchedTweet['gmt_tweet_date'].strftime('%d/%m/%Y')
                doc['gmt_tweet_hour'] = fetchedTweet['gmt_tweet_date'].strftime('%H')
                doc['screen_name'] = fetchedTweet['screen_name']
                doc['sentiment_class'] = fetchedTweet['sentiment_class']
                doc['class_probability'] = fetchedTweet['class_probability']
                tweets.append(InsertOne(doc))
        
        if len(tweets) > 0:
            #write the new records to the output collection        
            result = output_collection.bulk_write(tweets)
            logging.info("{}: Records added to mongoDB: {}".format(threadName,result.inserted_count))
        else:
            logging.info("{}: Records added to mongoDB: {}".format(threadName,len(tweets)))
    except Exception, e:
        print(e)
        sys.exit()

def process_days(threadName,stream,output_collection,next_date,end_date):
    try:
        logging.info("{}: Started fetching tweets for date: {}".format(threadName,next_date.strftime('%a %b %d %Y')))
        fetchedTweets = fetch_tweets(threadName,stream,output_collection,next_date,end_date)
        logging.info("{}: Finished fetching tweets ...".format(threadName))
        logging.info("{}: Started preprocessing tweets ...".format(threadName))
        preprocessedTweets = preprocess_tweets(fetchedTweets)
        logging.info("{}: Finished preprocessing tweets ...".format(threadName))
        logging.info("{}: Started extracting traffic sentiments ...".format(threadName))
        classify_tweets_sentiments(threadName,output_collection,preprocessedTweets)
        logging.info("{}: Finished extracting traffic sentiments ...".format(threadName))
            
    except Exception, e:
        print(e)
        sys.exit()

def parallel_process_days(start_date_str,end_date_str):
    global sentiment_classifier_filename
    global sentiment_vectorizer_filename
    gmt = timezone('GMT')
    try:
        stream = establish_connection_optimum("uk_accounts")
        output_collection = establish_connection_optimum("uk_accounts_tweet_sentiments")
        training_collection = establish_connection_optimum("SentiTrainingTweets")
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
    #check if the classifier and vectorizer exist. If not, build and persist them
    try:
        if os.path.isfile(sentiment_classifier_filename) and os.path.isfile(sentiment_vectorizer_filename):
            logging.info("classifier/vectorizer found and will be loaded from files")
        else:
            logging.info("classifier/vectorizer not found in files. Started generating classifier / vectorizer")
            train_senti_model(training_collection)
            logging.info("classifier/vectorizer generated and stored in files")
        
    except Exception, e:
        print(e)
        sys.exit()
        
        
    try:
        while next_date < gmt_e_date:
            end_date = next_date + datetime.timedelta(days=1)
            t = threading.Thread(target=process_days, args=("Thread-{}".format(next_date.strftime('%a-%b-%d-%Y')), 
                                                    stream, output_collection, next_date, end_date, ))
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
#    end_date_str = 'Mon May 23'
    parallel_process_days(start_date_str,end_date_str)
    logging.info("All Done!")

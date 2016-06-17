#!/usr/local/Cellar/python/2.7.11/bin/python

# Import classes from bcc_streaming package
from bcc_streaming import PushBccTrafficToLocalCollections
from bcc_streaming import PushBccTrafficToOptimumCollections
from datetime import datetime
import logging

logfile = '/Users/ahmadammari/Dropbox/Work/Optimum/bcc/bcc_streams.log'
# logfile = 'C:\\Users\\Optimum\\Documents\\bcc\\bcc_streams.log'
logging.basicConfig(filename=logfile,level=logging.INFO, format='%(asctime)s %(message)s')
 
if __name__ == '__main__':
    start = datetime.now()
    PushBccTrafficToLocalCollections.push_data_to_local_collections()   #localhost mongoDB
#    PushBccTrafficToOptimumCollections.push_data_to_optimum_collections() #Intrasoft's VM mongoDB
    end = datetime.now()
    msg = ",executiontime,%s" % ((end-start).total_seconds())
    logging.info(msg)
    
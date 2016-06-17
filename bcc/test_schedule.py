# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from bcc_streaming import PushBccTrafficToLocalCollections
from bcc_streaming import PushBccTrafficToOptimumCollections
from datetime import datetime
import logging
import schedule
import time

logfile = 'C:\\Users\\Optimum\\Documents\\bcc\\bcc_streams.log'
logging.basicConfig(filename=logfile,level=logging.INFO, format='%(asctime)s %(message)s')

def job():
    start = datetime.now()
    PushBccTrafficToLocalCollections.push_data_to_local_collections()   #localhost mongoDB
#    PushBccTrafficToOptimumCollections.push_data_to_optimum_collections() #Intrasoft's VM mongoDB
    end = datetime.now()
    msg = ",executiontime,%s" % ((end-start).total_seconds())
    logging.info(msg)
    print "Last runtime: %s\n" % (end.strftime("%Y-%m-%d %H:%M:%S"))

schedule.every(2).minutes.do(job)
    
while True:
    schedule.run_pending()
    time.sleep(1)
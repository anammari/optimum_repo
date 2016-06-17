# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from TwitterAggsIntra import TrafficMentionsUKAccountsHourlyAggregatesHighwayLevelIntraMT
from datetime import datetime
import logging
#import schedule
#import time

#logfile = 'C:\\Users\\Optimum\\Documents\\bcc\\bcc_streams.log'
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

def job(start_date_str, end_date_str, source):
    
    start = datetime.now()
    msg = "Started generating traffic aggregates (highway-level) for day: %s" % (start_date_str)
    TrafficMentionsUKAccountsHourlyAggregatesHighwayLevelIntraMT.parallel_process_days(start_date_str,end_date_str,source)
    end = datetime.now()
    msg = "Finished generating traffic aggregates (highway-level) for day: %s" % (start_date_str)
    logging.info(msg)
    msg = ",executiontime,%s" % ((end-start).total_seconds())
    logging.info(msg)
    
    

if __name__ == '__main__':
    start_date_str = 'Thu May 26'
    end_date_str = 'Fri May 27'
    source = "UKTraffic"
    job(start_date_str, end_date_str, source)
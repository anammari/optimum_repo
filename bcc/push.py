# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

from utils import pushBccRecords
import datetime
import logging

logfile = 'C:\\Users\\Optimum\\Documents\\bcc\\bcc_push.log' #UoW Windows server
logging.basicConfig(filename=logfile, level=logging.INFO, format='%(asctime)s %(message)s')

if __name__ == '__main__':
    start = datetime.datetime.now()
    pushBccRecords.push_bcc_traffic_data_to_optimum_db() 
    end = datetime.datetime.now()
    msg = "total execution time (sec): %s" % ((end-start).total_seconds())
    logging.info(msg)
    msg = "Last runtime: %s\n" % (end.strftime("%Y-%m-%d %H:%M:%S"))
    logging.info(msg)


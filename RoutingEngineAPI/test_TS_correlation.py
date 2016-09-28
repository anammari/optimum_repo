# -*- coding: utf-8 -*-
"""
Created on Wed Jun 08 17:19:07 2016

@author: Ahmad
"""

import pymongo
import pandas as pd
from pytz import timezone
import datetime
import logging
import sys
from bson.json_util import dumps
from bson import json_util
import matplotlib.pyplot as plt
import numpy as np

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

def establish_connection_optimum_collection(db_name, collection_name):
    try:
        # establish a connection to the collection
        host = "optimum.euprojects.net"
        port = 3368
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

def fetch_measurements(sensor_collection, sensorIds, m_type):
    gmt = timezone('GMT')
    try:
        endDt = datetime.datetime.now()
        gmt_e_date = gmt.localize(endDt)
        
        #start date is a month before the end date
        gmt_s_date = gmt_e_date - datetime.timedelta(hours=12)
        
#        print startDt
#        print endDt
    
    except Exception, e:
        print(e)
        sys.exit()
    
    logging.info("Fetching 1 day of {} measurements from each sensor".format(m_type))
    
    measurements = {}
    try:
        for sensorId in sensorIds:
            query = {"measurement_id" : sensorId,
                     "type" : m_type,
                     "measurement_datetime":     {"$gte": gmt_s_date,
                                                  "$lt": gmt_e_date}}
            project = {"measurement_datetime": 1, "value": 1, "_id": 0}
            logging.info("Started fetching {} for sensor {}".format(m_type,sensorId))                                     
            cursor = sensor_collection.find(query,project)
            #print for testing
    #        print dumps(cursor, indent=2, default=json_util.default)
            
            # Expand the cursor and construct the DataFrame
            df =  pd.DataFrame(list(cursor))
            df
            measurements[sensorId] = df
            logging.info("Finished fetching {} for sensor {}".format(m_type,sensorId))
    except Exception, e:
        print(e)
        sys.exit()
    
    return measurements

def compute_correlations(measurements):
    try:
        sensorIds = measurements.keys()
        for sensorId in sensorIds:
            for measurement in measurements.keys():
                logging.info("Correlation of {} and {}: {:0.4f}".format(sensorId,
                                                                        measurement,
                                                                        measurements[sensorId].corrwith(measurements[measurement], method="kendall").value))
    except Exception, e:
        print(e)
        sys.exit()         
            

if __name__ == '__main__':
    sensorIds = ['N13112Y', 'N13141W', 'N14111Y', 'N13111A', 'N14122C']
#    sensorIds = ['N13112Y']
    m_type = 'AverageSpeed'
    sensor_collection = establish_connection_optimum_collection("BccTraffic", "roadSensorValue")
    measurements = fetch_measurements(sensor_collection, sensorIds, m_type)
    compute_correlations(measurements)
    

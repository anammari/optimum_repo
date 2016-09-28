# -*- coding: utf-8 -*-
"""
Created on Mon Jun 27 2016

@author: Ahmad
"""

import requests
import pandas as pd
from datetime import timedelta
import datetime
import xml.etree.ElementTree as ET
from pymongo import InsertOne
import pymongo
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

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

def establish_connection_optimum(db_name, collection_name):
    try:
        # establish a connection to the collection
        host = "optimum.euprojects.net"
        port = 3368
#        host = "192.168.3.50"
#        port = 27017
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

def get_POST_responses(atcoCodes):
    responses = []
    i = datetime.datetime.now()
#    i = i - datetime.timedelta(hours=1) 
    iStr = i.strftime("%Y-%m-%dT%H:%M:%S+01:00")
    for code in atcoCodes:
        url = "http://TravelineAPI336:s4HaKB7I@nextbus.mxdata.co.uk/nextbuses/1.0/1"
        xml = ""
        xml = xml + '<?xml version="1.0" encoding="UTF-8"?>'
        xml = xml + '<Siri xmlns="http://www.siri.org.uk/" version="1.0">'
        xml = xml + '   <ServiceRequest>'
        xml = xml + '      <RequestTimestamp>%s</RequestTimestamp>' % (iStr)
        xml = xml + '      <RequestorRef>TravelineAPI336</RequestorRef>'
        xml = xml + '      <StopMonitoringRequest version="1.0">'
        xml = xml + '         <RequestTimestamp>%s</RequestTimestamp>' % (iStr)
        xml = xml + '         <MessageIdentifier>12345</MessageIdentifier>'
        xml = xml + '         <MonitoringRef>%s</MonitoringRef>' % (code)
        xml = xml + '      </StopMonitoringRequest>'
        xml = xml + '   </ServiceRequest>'
        xml = xml + '</Siri>'
        xml = xml.replace('\n', '').replace('\r', '')    
        xml = unicode(xml, "utf-8")
        headers = {'Content-Type':'text/xml; charset=UTF-8'}
        
        r = requests.post(url, data=xml, headers=headers)
        responses.append(r)
    
    return responses

def parse_StopMonitoringDelivery(responses,output_collection):
  for response in responses:
      root = ET.fromstring(response.text)
      parse_XML(root,output_collection)

def parse_file(filename,output_collection):
  tree = ET.parse(filename)
  root = tree.getroot()
  parse_XML(root,output_collection)

def parse_XML(root,output_collection):
  atcoCode = ''
  allServiceDeliveriesList = root.findall('{http://www.siri.org.uk/}ServiceDelivery')
#  print type(allServiceDeliveries)
  if len(allServiceDeliveriesList) > 0:
      allServiceDeliveries = allServiceDeliveriesList[0]
      StopMonitoringDeliveryList=allServiceDeliveries.findall('{http://www.siri.org.uk/}StopMonitoringDelivery')
      if len(StopMonitoringDeliveryList) > 0:
          StopMonitoringDeliveryElem = StopMonitoringDeliveryList[0]
          MonitoredStopVisitList = StopMonitoringDeliveryElem.findall('{http://www.siri.org.uk/}MonitoredStopVisit')
          if len(MonitoredStopVisitList) > 0:
              mongoRecords = []
              for i in range(0,len(MonitoredStopVisitList)):
                  mongoRec = {}
                  MonitoredStopVisitElem = MonitoredStopVisitList[i]
                  MonitoringRef = MonitoredStopVisitElem.find('{http://www.siri.org.uk/}MonitoringRef')
                  mongoRec['MonitoringRef'] = MonitoringRef.text
                  atcoCode = MonitoringRef.text
                  MonitoredVehicleJourneyElem = MonitoredStopVisitElem.find('{http://www.siri.org.uk/}MonitoredVehicleJourney')
                  VehicleMode = MonitoredVehicleJourneyElem.find('{http://www.siri.org.uk/}VehicleMode')
                  mongoRec['VehicleMode'] = VehicleMode.text
                  PublishedLineName = MonitoredVehicleJourneyElem.find('{http://www.siri.org.uk/}PublishedLineName')
                  mongoRec['PublishedLineName'] = PublishedLineName.text
                  DirectionName = MonitoredVehicleJourneyElem.find('{http://www.siri.org.uk/}DirectionName')
                  mongoRec['DirectionName'] = DirectionName.text
                  OperatorRef = MonitoredVehicleJourneyElem.find('{http://www.siri.org.uk/}OperatorRef')
                  mongoRec['OperatorRef'] = OperatorRef.text
                  MonitoredCallElem = MonitoredVehicleJourneyElem.find('{http://www.siri.org.uk/}MonitoredCall')
                  if len(MonitoredCallElem) == 1:
                      AimedDepartureTime = MonitoredCallElem.find('{http://www.siri.org.uk/}AimedDepartureTime')
                      AimedDepartureTimeStr = AimedDepartureTime.text
                      AimedDepartureTimeDt = datetime.datetime.strptime(AimedDepartureTimeStr, '%Y-%m-%dT%H:%M:%S.000+01:00')
                      mongoRec['AimedDepartureTime'] =  AimedDepartureTimeDt
                  elif len(MonitoredCallElem) == 2:
                      AimedDepartureTime = MonitoredCallElem.find('{http://www.siri.org.uk/}AimedDepartureTime')
                      AimedDepartureTimeStr = AimedDepartureTime.text
                      AimedDepartureTimeDt = datetime.datetime.strptime(AimedDepartureTimeStr, '%Y-%m-%dT%H:%M:%S.000+01:00')
                      mongoRec['AimedDepartureTime'] =  AimedDepartureTimeDt
                      ExpectedDepartureTime = MonitoredCallElem.find('{http://www.siri.org.uk/}ExpectedDepartureTime')
                      ExpectedDepartureTimeStr = ExpectedDepartureTime.text
                      ExpectedDepartureTimeDt = datetime.datetime.strptime(ExpectedDepartureTimeStr, '%Y-%m-%dT%H:%M:%S.000+01:00')
                      mongoRec['ExpectedDepartureTime'] =  ExpectedDepartureTimeDt
                  mongoRecords.append(InsertOne(mongoRec))
              if len(mongoRecords) > 0:
                  writeMongo(mongoRecords,output_collection,atcoCode)

def writeMongo(mongoRecords,output_collection,atcoCode):
    result = output_collection.bulk_write(mongoRecords)
    logging.info("Records added for bus stop {} to collection {}: {}".format(atcoCode,output_collection.name,result.inserted_count))    
    
def main():
    output_collection = establish_connection_optimum("PublicTransportUK", "monitoredStopVisitsBirm")
    atcoCodes = get_column_data("nearest_stops.csv",0)
    responses = get_POST_responses(atcoCodes[0:2])
    parse_StopMonitoringDelivery(responses,output_collection)
#    parse_file("StopMonitoringDelivery_43000252103.xml",output_collection)


if __name__ == "__main__":
  main()

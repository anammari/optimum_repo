# -*- coding: utf-8 -*-
"""
Testing Traveline API with the Python requests library

"""
import requests
import datetime

def get_POST_responses(atcoCode):
    i = datetime.datetime.now() 
    iStr = i.strftime("%Y-%m-%dT%H:%M:%SZ")
    print iStr
    url = "http://TravelineAPI336:s4HaKB7I@nextbus.mxdata.co.uk/nextbuses/1.0/1"
#    xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Siri xmlns="http://www.siri.org.uk/" version="1.0"><ServiceRequest><RequestTimestamp>%s</RequestTimestamp><RequestorRef>TravelineAPI336</RequestorRef><StopMonitoringRequest version="1.0"><RequestTimestamp>%s</RequestTimestamp><MessageIdentifier>12345</MessageIdentifier><MonitoringRef>%s</MonitoringRef></StopMonitoringRequest></ServiceRequest></Siri>"""%(iStr,iStr,atcoCode)
    xml = ""
    xml = xml + '<?xml version="1.0" encoding="UTF-8"?>'
    xml = xml + '<Siri xmlns="http://www.siri.org.uk/" version="1.0">'
    xml = xml + '   <ServiceRequest>'
    xml = xml + '      <RequestTimestamp>%s</RequestTimestamp>' % (iStr)
    xml = xml + '      <RequestorRef>TravelineAPI336</RequestorRef>'
    xml = xml + '      <StopMonitoringRequest version="1.0">'
    xml = xml + '         <RequestTimestamp>%s</RequestTimestamp>' % (iStr)
    xml = xml + '         <MessageIdentifier>12345</MessageIdentifier>'
    xml = xml + '         <MonitoringRef>%s</MonitoringRef>' % (atcoCode)
    xml = xml + '      </StopMonitoringRequest>'
    xml = xml + '   </ServiceRequest>'
    xml = xml + '</Siri>'
    xml = xml.replace('\n', '').replace('\r', '')    
    xml = unicode(xml, "utf-8")
#    print xml
    headers = {'Content-Type':'text/xml; charset=UTF-8'}
#    headers = {'Content-Type':'text/xml'}
    
    r = requests.post(url, data=xml, headers=headers)
    
    return r

def main():
  atcoCode = "43000252103"
  response = get_POST_responses(atcoCode)
  print response.status_code
  print response.headers
  print response.text
  
#  send_xml()
 
if __name__ == "__main__":
  main()

import requests
import xml.etree.ElementTree as ET
import math
from datetime import datetime, timedelta 
from math import sqrt, pi, sin, cos, tan, atan2 as arctan2
import csv

def calculate_initial_compass_bearing(pointA, pointB):
   """
   Calculates the bearing between two points.
   The formulae used is the following:
   θ = atan2(sin(Δlong).cos(lat2),
   cos(lat1).sin(lat2) − sin(lat1).cos(lat2).cos(Δlong))
   :Parameters:
   - `pointA: The tuple representing the latitude/longitude for the
   first point. Latitude and longitude must be in decimal degrees
   - `pointB: The tuple representing the latitude/longitude for the
   second point. Latitude and longitude must be in decimal degrees
   :Returns:
   The bearing in degrees
   :Returns Type:
   float
   """
   if (type(pointA) != tuple) or (type(pointB) != tuple):
	  raise TypeError("Only tuples are supported as arguments")

   lat1 = math.radians(pointA[0])
   lat2 = math.radians(pointB[0])

   diffLong = math.radians(pointB[1] - pointA[1])

   x = math.sin(diffLong) * math.cos(lat2)
   y = math.cos(lat1) * math.sin(lat2) - (math.sin(lat1) * math.cos(lat2) * math.cos(diffLong))

   initial_bearing = math.atan2(x, y)

   # Now we have the initial bearing but math.atan2 return values
   # from -180° to + 180° which is not what we want for a compass bearing
   # The solution is to normalize the initial bearing as shown below
   initial_bearing = math.degrees(initial_bearing)
   compass_bearing = (initial_bearing + 360) % 360

   return compass_bearing
   
def today():
    i = datetime.now()
    day = str(i.day)
    if len(day) == 1: day = '0' + day
    month = str(i.month)
    if len(month) == 1: month = '0' + month
    today = ("%s%s%s_" % (i.year, month, day))
    return today

def OSGB36toWGS84(E,N):
   #E, N are the British national grid coordinates - eastings and northings
   a = 6377563.396
   b = 6356256.909
   #The Airy 180 semi-major and semi-minor axes used for OSGB36 (m)
   F0 = 0.9996012717
   lat0 = 49*pi/180
   lon0 = -2*pi/180
   N0, E0 = -100000, 400000
   e2 = 1 - (b*b)/(a*a)
   n = (a-b)/(a+b)

   #Initialise the iterative variables
   lat,M = lat0, 0

   while N-N0-M >= 0.00001:
	  lat = (N-N0-M)/(a*F0) + lat;
	  M1 = (1 + n + (5./4)*n**2 + (5./4)*n**3) * (lat-lat0)
	  M2 = (3*n + 3*n**2 + (21./8)*n**3) * sin(lat-lat0) * cos(lat+lat0)
	  M3 = ((15./8)*n**2 + (15./8)*n**3) * sin(2*(lat-lat0)) * cos(2*(lat+lat0))
	  M4 = (35./24)*n**3 * sin(3*(lat-lat0)) * cos(3*(lat+lat0))
	  #meridional arc
	  M = b * F0 * (M1 - M2 + M3 - M4)

   #transverse radius of curvature
   nu = a*F0/sqrt(1-e2*sin(lat)**2)

   #meridional radius of curvature
   rho = a*F0*(1-e2)*(1-e2*sin(lat)**2)**(-1.5)
   eta2 = nu/rho-1

   secLat = 1./cos(lat)
   VII = tan(lat)/(2*rho*nu)
   VIII = tan(lat)/(24*rho*nu**3)*(5+3*tan(lat)**2+eta2-9*tan(lat)**2*eta2)
   IX = tan(lat)/(720*rho*nu**5)*(61+90*tan(lat)**2+45*tan(lat)**4)
   X = secLat/nu
   XI = secLat/(6*nu**3)*(nu/rho+2*tan(lat)**2)
   XII = secLat/(120*nu**5)*(5+28*tan(lat)**2+24*tan(lat)**4)
   XIIA = secLat/(5040*nu**7)*(61+662*tan(lat)**2+1320*tan(lat)**4+720*tan(lat)**6)
   dE = E-E0

   #These are on the wrong ellipsoid currently: Airy1830. (Denoted by _1)
   lat_1 = lat - VII*dE**2 + VIII*dE**4 - IX*dE**6
   lon_1 = lon0 + X*dE - XI*dE**3 + XII*dE**5 - XIIA*dE**7

   #Want to convert to the GRS80 ellipsoid. 
   #First convert to cartesian from spherical polar coordinates
   H = 0
   x_1 = (nu/F0 + H)*cos(lat_1)*cos(lon_1)
   y_1 = (nu/F0+ H)*cos(lat_1)*sin(lon_1)
   z_1 = ((1-e2)*nu/F0 +H)*sin(lat_1)

   #Perform Helmut transform (to go between Airy 1830 (_1) and GRS80 (_2))
   s = -20.4894*10**-6
   tx, ty, tz = 446.448, -125.157, + 542.060
   rxs,rys,rzs =0.1502,0.2470,0.8421
   rx, ry, rz = rxs*pi/(180*3600.), rys*pi/(180*3600.), rzs*pi/(180*3600.)
   x_2 = tx + (1+s)*x_1 + (-rz)*y_1 + (ry)*z_1
   y_2 = ty+(rz)*x_1+(1+s)*y_1+(-rx)*z_1
   z_2 = tz+(-ry)*x_1+(rx)*y_1+(1+s)*z_1

   #Back to spherical polar coordinates from cartesian
   #Need some of the characteristics of the new ellipsoid    
   a_2, b_2 =6378137.000, 6356752.3141
   e2_2 = 1- (b_2*b_2)/(a_2*a_2)
   p = sqrt(x_2**2 + y_2**2)

   #Lat is obtained by an iterative proceedure:   
   lat = arctan2(z_2,(p*(1-e2_2)))
   latold = 2*pi
   while abs(lat - latold)>10**-16:
	  lat, latold = latold, lat
	  nu_2 = a_2/sqrt(1-e2_2*sin(latold)**2)
	  lat = arctan2(z_2+e2_2*nu_2*sin(latold), p)

   #Lon and height are then pretty easy
   lon = arctan2(y_2,x_2)
   H = p/cos(lat) - nu_2

   #Convert to degrees
   lat = lat*180/pi
   lon = lon*180/pi

   #Job's a good'n. 
   return lat, lon

#download all the ways with sensors from overpass API 
#url = "http://www.overpass-api.de/api/xapi?way[bbox=-2.1691,52.3088,-1.5930,52.6801][traffic:sensor:ref=*]"
url = "http://www.overpass-api.de/api/xapi?way[bbox=-2.1808,52.3362,-1.6562,52.5905][traffic:sensor:ref=*]"
r = requests.get(url)
root = ET.fromstring(r.content)


#find the start and end nodes of a way
allways=root.findall('way')
bearinglookup={}
for way in allways:
   startway="none"
   currentway="none"
   endway="none"
   sensorreflanes=[]
   startlat=0
   startlon=0
   endlat=0
   endlon=0
   for tag in way.findall('nd'):
	  if startway=="none":
		 startway=tag.get('ref')
		 currentway=startway
	  else:
		 currentway=tag.get('ref')
   endway=currentway
   #get the attributes for the sensor from the way tag
   for tag in way.findall('tag'):
	  if tag.get('k')=='traffic:sensor:ref':
		 sensorreflanes.append(tag.attrib['v'])
	  if tag.get('k')=='traffic:sensor:ref_1':
		 sensorreflanes.append(tag.attrib['v'])
	  if tag.get('k')=='traffic:sensor:ref_2':
		 sensorreflanes.append(tag.attrib['v'])
	  if tag.get('k')=='traffic:sensor:ref_3':
		 sensorreflanes.append(tag.attrib['v'])
   allnodes=root.findall('node')
   #get the locations of the start and end nodes
   for node in allnodes:
	  if node.get('id')==startway:
		 startlat=node.attrib['lat']
		 startlon=node.attrib['lon']
	  if node.get('id')==endway:
		 endlat=node.attrib['lat']
		 endlon=node.attrib['lon']
   pointA=(float(startlat),float(startlon)        )
   pointB=(float(endlat),float(endlon))           
   #calculate the bearings
   bearing=calculate_initial_compass_bearing(pointA, pointB)            
   #split the sensor information into lanes
   #newlist=sensorreflanes.split('|')
   newlist=sensorreflanes    
   #Try to process it so that backward lanes have their bearing reversed (this might not work for all cases)
   currval="none"
   for n in newlist:
	  if n=="no":
		 bearing=bearing+180
		 if bearing>360:
			bearing=bearing-360
	  if currval=="none":
		 if n<>"no":
			#print n, bearing
			bearinglookup[n]=bearing
			currval=n
	  if n<>currval:
		 if n<>"no":
			bearing=bearing+180
			if bearing>360:
			   bearing=bearing-360
			   #print n, bearing
			   bearinglookup[n]=bearing
			   currval=n
#Download current flow data from the adaptor logic site
z=0
y=0
x = datetime.now()
print x
x=x-timedelta(days=1)
url = "http://butc.opendata.onl/UTMC averagespeed.xml"
r = requests.get(url)
print len(r.content)
#Download the node information from Overpass (we could probably reuse the way stuff from earlier) 
root = ET.fromstring(r.content)
#urlosm = "http://www.overpass-api.de/api/xapi?way[bbox=-2.1691,52.3088,-1.5930,52.6801][traffic:sensor:ref=*]"
urlosm = "http://www.overpass-api.de/api/xapi?way[bbox=-2.1808,52.3362,-1.6562,52.5905][traffic:sensor:ref=*]"
rosm = requests.get(urlosm)
rootosm = ET.fromstring(rosm.content)
allnodesosm=rootosm.findall('way')
#Get rid of all the data that is older than a day
f = open(today()+"sensorDetectorDirections.csv", "wb")
lines = []
line = '{},{},{},{},{},{},{}'.format('scnno', 'timestamp', 'value' , 'lat', 'lon', 'bearinglookup','bearing')
lines.append(line)
for flow in root.iter('AverageSpeed'):
    timestamp=datetime.strptime(flow[4].text,'%Y-%m-%d %H:%M:%S')
    if timestamp > x:                              
		scnno=flow[0].text
		z=z+1
		easting=float(flow[3].text)
		northing=float(flow[3].text)
		lat,lon=0,0
	    #convert easting and northing to WGS84 if data available, otherwise get it from openstreetmap
		if easting<>0:
			lat, lon = OSGB36toWGS84(float(flow[3].text), float(flow[2].text))
		else:
			for node in allnodesosm:
				for tag in node.findall('tag'):
					if tag.get('k')=='traffic:sensor:ref':
						foundtag=tag.attrib['v']
						if foundtag==scnno:                                      
							lat=node.get('lat')
							lon=node.get('lon')
		if lat<>0:                                            
			if scnno in bearinglookup:
				if (bearinglookup[scnno]>22.5 and bearinglookup[scnno]<67.5):
					genbearing="NE"
				elif (bearinglookup[scnno]>67.5 and bearinglookup[scnno]<112.5):
					genbearing="E"
				elif (bearinglookup[scnno]>112.5 and bearinglookup[scnno]<157.5):
					genbearing="SE"
				elif (bearinglookup[scnno]>157.5 and bearinglookup[scnno]<202.5):
					genbearing="S"
				elif (bearinglookup[scnno]>202.5 and bearinglookup[scnno]<247.5):
					genbearing="SW"
				elif (bearinglookup[scnno]>247.5 and bearinglookup[scnno]<292.5):
					genbearing="W"
				elif (bearinglookup[scnno]>292.5 and bearinglookup[scnno]<337.5):
					genbearing="NW"
				else:
					genbearing="N"
				line = '{},{},{},{},{},{},{}'.format(scnno, flow[4].text, flow[5][0].text, lat, lon, int(bearinglookup[scnno]),genbearing)
				lines.append(line)
				print scnno, flow[4].text, flow[5][0].text, lat, lon, int(bearinglookup[scnno]),genbearing,'\r\n'
			else:
				line = '{},{},{},{},{}'.format(scnno, flow[4].text, flow[5][0].text, lat, lon)
				lines.append(line)
				print scnno, flow[4].text, flow[5][0].text, lat, lon,'\r\n'
		else:
			y=y+1 
w = csv.writer(f, delimiter = ',')
w.writerows([xx.split(',') for xx in lines])
f.close()			 
print "working detectors",z
print "unfound co-ordinates",y    

#write it all down nicely, with bearing if we have one. This will go into a nice datastructure for upload (later). I also add some cheeky generalisation of the bearing.
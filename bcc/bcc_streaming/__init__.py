# -*- coding: utf-8 -*-
"""
Created on Thu Feb 18 17:15:46 2016

@author: Ahmad

This is a Python package to stream Birmingham City Council Data and store them into mongoDB collections

Contents:
    - pushBccDataToMongoFirstTime.py: utility script to insert the data for the first time into an empty DB.
    - pushBccAnprToMongoFirstTime.py: utility script to insert the ANPR data for the first time into an empty DB.
    - PushBccTrafficToOptimumCollections.py: script to update the DB (Optimum VM) with new records. This should be run as
    a cron job every 2 minutes. This script assumes remote processing (script and mongoDB are on different machines).
    - PushBccTrafficToLocalCollections.py: script to update the DB (localhost) with new records. This should be run as
    a cron job every 2 minutes. This script assumes local processing (script and mongoDB are on same machine).
    - ENtoLL.py: utility script to convert geolocation data between UK Easting / Northing coordinates and 
    Latitude / Longitude.
"""

import PushBccTrafficToOptimumCollections
import PushBccTrafficToLocalCollections

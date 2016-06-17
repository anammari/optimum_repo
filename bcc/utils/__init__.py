# -*- coding: utf-8 -*-
"""
Created on Thu Feb 18 17:15:46 2016

@author: Ahmad

This is a Python package to push Birmingham City Council Data (roadSensorData) 
from UoW mongoDB server to Optimum (Intrasoft) mongoDB server

Contents:
    - pushBccRecords: scheduled push of existing BCC Traffic records on UoW server datastore in 5 traffic-related collections 
        to Optimum VM server mongoDB.
"""

import pushBccRecords


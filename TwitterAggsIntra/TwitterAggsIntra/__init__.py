# -*- coding: utf-8 -*-
"""
Created on Thu May 26, 2016

@author: Ahmad

This is a Python package to aggregate Twitter features and store them into mongoDB collections

Contents:
    - HighwayMentionsRegexUKAccountsMongoIntraDaysMT.py: generates highway mentions in tweets.
    - TrafficMentionsUKAccountsMongoIntraDaysMT.py: generates traffic concepts based on traffic term mentions in tweets.
    - HighwayMentionsRegexUKAccountsHourlyAggregatesIntraMT.py: hourly aggregations of highway mentions
    - TrafficMentionsUKAccountsHourlyAggregatesAllHighwaysIntraMT.py: hourly aggregations of traffic concepts (all highways)
    - TrafficMentionsUKAccountsHourlyAggregatesHighwayLevelIntraMT.py: hourly aggregations of traffic concepts (highway level)
"""

import HighwayMentionsRegexUKAccountsMongoIntraDaysMT
import TrafficMentionsUKAccountsMongoIntraDaysMT
import HighwayMentionsRegexUKAccountsHourlyAggregatesIntraMT
import TrafficMentionsUKAccountsHourlyAggregatesAllHighwaysIntraMT
import TrafficMentionsUKAccountsHourlyAggregatesHighwayLevelIntraMT

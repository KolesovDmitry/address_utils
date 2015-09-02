#!/bin/env python
# -*- coding: utf-8 -*-

import os

# Location of test data
currdir = os.path.dirname(__file__)

DATANAME = 'testdata'
DATADIR = os.path.join(currdir, DATANAME)

COUNTRY_LIST = os.path.join(DATADIR, 'countries.csv')
REGION_LIST = os.path.join(DATADIR, 'regions.csv')
SUBREGION_LIST = os.path.join(DATADIR, 'subregions.csv')
CITY_LIST = os.path.join(DATADIR, 'cities.csv')
STREET_LIST = os.path.join(DATADIR, 'streets.csv')
HOUSE_LIST = os.path.join(DATADIR, 'houses.csv')
POI_LIST = os.path.join(DATADIR, 'poi.csv')

TMPFILE = os.path.join(DATADIR, 'tmp.csv')

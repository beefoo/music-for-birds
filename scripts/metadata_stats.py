# -*- coding: utf-8 -*-

import argparse
import collections
import csv
from matplotlib import pyplot as plt
import os
import numpy as np
from pprint import pprint
import sys
from utils import readCsv

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="../data/output/birds_audio_metadata.csv", help="Input csv file")
parser.add_argument('-top', dest="SHOW_TOP", default=10, type=int, help="Show most common X")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/output/birds_audio_metadata_%s.csv", help="Output csv file pattern")
args = parser.parse_args()

INPUT_FILE = args.INPUT_FILE
SHOW_TOP = args.SHOW_TOP
OUTPUT_FILE = args.OUTPUT_FILE

print("Reading data file...")
data = readCsv(INPUT_FILE)
rowCount = len(data)
print("Found %s rows in %s" % (rowCount, INPUT_FILE))

places = []
groups = []
tags = []
for entry in data:

    # add places
    state = entry["state"]
    country = entry["country"]
    if country == "United States":
        places.append(state)
    else:
        places.append(country)

    # add groups
    groups += [g.lower() for g in entry["groups"].split(", ")]

    # add tags
    description = entry["description"].replace(" and ", " ")
    description = description.replace(",", "")
    tags += [t.strip().lower() for t in description.split(" ")]

print("TOP %s PLACES:" % SHOW_TOP)
placeCounter = collections.Counter(places)
pprint(placeCounter.most_common(SHOW_TOP))
print "====="

print("TOP %s GROUPS:" % SHOW_TOP)
groupCounter = collections.Counter(groups)
pprint(groupCounter.most_common(SHOW_TOP))
print "====="

print("TOP %s TAGS:" % SHOW_TOP)
tagCounter = collections.Counter(tags)
pprint(tagCounter.most_common(SHOW_TOP))

def writeCsv(filename, data, headings):
    with open(filename, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(headings)
        rows = [list(d) for d in data]
        writer.writerows(rows)
        print "Wrote %s rows to %s" % (len(rows), filename)

headings = ["Value", "Frequency"]
writeCsv(OUTPUT_FILE % "places", placeCounter.most_common(), headings)
writeCsv(OUTPUT_FILE % "groups", groupCounter.most_common(), headings)
writeCsv(OUTPUT_FILE % "tags", tagCounter.most_common(), headings)

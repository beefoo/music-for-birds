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
parser.add_argument('-in', dest="INPUT_FILE", default="../data/output/birds_audio_samples.csv", help="Input csv file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/output/birds_audio_sample_stats.csv", help="Output csv file")
args = parser.parse_args()

INPUT_FILE = args.INPUT_FILE
OUTPUT_FILE = args.OUTPUT_FILE

print("Reading data file...")
data = readCsv(INPUT_FILE)
rowCount = len(data)
print("Found %s rows in %s" % (rowCount, INPUT_FILE))

# keys: parent,start,dur,power,hz,note,octave

notes = []
octaves = []
x = []
y = []
for entry in data:
    notes.append(entry["note"])
    octaves.append(entry["octave"])
    x.append(entry["power"])
    y.append(entry["hz"])

print("TOP NOTES:")
noteCounter = collections.Counter(notes)
pprint(noteCounter.most_common())
print "====="

print("TOP %s OCTAVES:")
octaveCounter = collections.Counter(octaves)
pprint(octaveCounter.most_common())
print "====="

# show scatter plot of data
plt.scatter(x, y, alpha=0.2)
plt.xlabel("Power")
plt.ylabel("Frequency (Hz)")
plt.show()

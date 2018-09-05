# -*- coding: utf-8 -*-

import argparse
import collections
import csv
import os
import numpy as np
from pprint import pprint
import sys
from utils import readCsv

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="../data/output/birds_audio_samples.csv", help="Input csv file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/output/birds_audio_sample_stats.csv", help="Output csv file")
parser.add_argument('-plot', dest="PLOT", default=0, type=int, help="Whether to show plot")
args = parser.parse_args()

INPUT_FILE = args.INPUT_FILE
OUTPUT_FILE = args.OUTPUT_FILE
PLOT = args.PLOT > 0

print("Reading data file...")
data = readCsv(INPUT_FILE)
rowCount = len(data)
print("Found %s rows in %s" % (rowCount, INPUT_FILE))

# keys: parent,start,dur,power,hz,note,octave

notes = []
octaves = []
noteOctaves = []
x = []
y = []
for entry in data:
    notes.append(entry["note"])
    octaves.append(entry["octave"])
    noteOctaves.append(entry["note"]+str(entry["octave"]))
    x.append(entry["power"])
    y.append(entry["hz"])

print("NOTES:")
noteCounter = collections.Counter(notes)
pprint(noteCounter.most_common())
print "====="

print("OCTAVES:")
octaveCounter = collections.Counter(octaves)
pprint(octaveCounter.most_common())
print "====="

print("NOTES WITH OCTAVES:")
noteOctaveCounter = collections.Counter(noteOctaves)
pprint(noteOctaveCounter.most_common(20))
print "====="

# show scatter plot of data
if PLOT:
    from matplotlib import pyplot as plt
    plt.scatter(x, y, alpha=0.2)
    plt.xlabel("Power")
    plt.ylabel("Frequency (Hz)")
    plt.show()

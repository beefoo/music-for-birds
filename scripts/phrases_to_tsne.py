# -*- coding: utf-8 -*-

import argparse
import csv
import glob
import json
from matplotlib import pyplot as plt
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import os
from os.path import join
import numpy as np
from pprint import pprint
from sklearn.manifold import TSNE
import sys
from utils import readCsv

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="../data/output/birds_audio_phrases.csv", help="Input csv file")
parser.add_argument('-plot', dest="PLOT", default=0, type=int, help="Show plot?")
parser.add_argument('-highlight', dest="HIGHLIGHT", default="notes", help="What to highlight: notes, files")
parser.add_argument('-saved', dest="SAVE_DATA", default=0, type=int, help="Save data files?")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/output/birds_phrases_tsne.csv", help="CSV output file")
args = parser.parse_args()

# Parse arguments
INPUT_FILE = args.INPUT_FILE
PLOT = args.PLOT > 0
HIGHLIGHT = args.HIGHLIGHT
SAVE_DATA = args.SAVE_DATA > 0
OUTPUT_FILE = args.OUTPUT_FILE

# Read files
print("Reading data file...")
data = readCsv(INPUT_FILE)
rowCount = len(data)
print("Found %s rows in %s" % (rowCount, INPUT_FILE))

# entry keys: parent,start,dur,phrase
# phrase keys: start,dur,power,hz,note,octave

for i, entry in enumerate(data):
    phrase = [v.split(":") for v in entry["phrase"].split(",")]
    for j, v in enumerate(phrase):
        phrase[j] = {
            "start": int(v[0]),
            "dur": int(v[1]),
            "power": float(v[2]),
            "hz": float(v[3]),
            "note": v[4],
            "octave": int(v[5]),
        }
    data[i]["phrase"] = phrase

# Make sure output dirs exist
outDirs = [os.path.dirname(OUTPUT_FILE)]
for outDir in outDirs:
    if not os.path.exists(outDir):
        os.makedirs(outDir)

def getFeatures(phrase):
    feature_vector = []
    hzs = [d["hz"] for d in phrase]
    durs = [d["dur"] for d in phrase]
    pows = [d["power"] for d in phrase]
    rests = []
    for j, d in enumerate(phrase):
        if j > 0:
            prev = phrase[j-1]
            rests.append(d["start"]-(prev["start"]+prev["dur"]))
    feature_vector.append(len(phrase))
    feature_vector.append(np.mean(hzs))
    feature_vector.append(np.mean(pows))
    feature_vector.append(np.mean(durs))
    feature_vector.append(np.mean(rests))
    feature_vector.append(np.std(hzs))
    feature_vector.append(np.std(pows))
    feature_vector.append(np.std(durs))
    feature_vector.append(np.std(rests))
    # pprint(feature_vector)
    return feature_vector

progress = 0
def doTSNE(row):
    global progress
    global rowCount

    featureData = getFeatures(row["phrase"])

    progress += 1
    sys.stdout.write('\r')
    sys.stdout.write("%s%%" % round(1.0*progress/rowCount*100,1))
    sys.stdout.flush()

    return featureData

# data = data[:10]
# for fn in files:
#     doTSNE(fn)
pool = ThreadPool()
featureVectors = pool.map(doTSNE, data)
pool.close()
pool.join()
# sys.exit(1)

model = TSNE(n_components=2,
             learning_rate=150, # increase if too dense, decrease if too uniform
             verbose=1,
             angle=0.1 # increase to make faster, decrease to make more accurate
).fit_transform(featureVectors)

x = model[:,0]
y = model[:,1]

if SAVE_DATA:
    print("Writing data to file...")
    headings = ["parent", "start", "dur", "x", "y"]

    # normalize data
    minX = np.min(x)
    maxX = np.max(x)
    minY = np.min(y)
    maxY = np.max(y)
    x_norm = (x - minX) / (maxX - minX)
    y_norm = (y - minY) / (maxY - minY)
    precision = 5

    with open(OUTPUT_FILE, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(headings)
        for i, d in enumerate(data):
            writer.writerow([d["parent"], d["start"], d["dur"], round(x_norm[i], precision), round(y_norm[i], precision)])
    print("Wrote %s rows to %s" % (rowCount, OUTPUT_FILE))

if PLOT:
    plt.figure(figsize = (10,10))
    plt.scatter(x, y)
    plt.show()

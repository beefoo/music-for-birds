# -*- coding: utf-8 -*-

import argparse
import csv
import glob
import json
import librosa
from matplotlib import pyplot as plt
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import os
from os.path import join
import numpy as np
from pprint import pprint
from sklearn.manifold import TSNE
import sys
from utils import getAudioSamples

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILES", default="../audio/sample/*.mp3", help="Input file pattern")
parser.add_argument('-adir', dest="INPUT_AUDIO_DIR", default="../audio/downloads/birds/%s.mp3", help="Input audio directory (if applicable)")
parser.add_argument('-samples', dest="SAMPLES", default=8, type=int, help="Max samples to produce, -1 for all")
parser.add_argument('-min', dest="MIN_DUR", default=0.05, type=float, help="Minimum sample duration in seconds")
parser.add_argument('-max', dest="MAX_DUR", default=1.00, type=float, help="Maximum sample duration in seconds")
parser.add_argument('-amp', dest="AMP_THESHOLD", default=-1, type=float, help="Amplitude theshold, -1 for default")
parser.add_argument('-plot', dest="PLOT", default=0, type=int, help="Show plot?")
parser.add_argument('-saved', dest="SAVE_DATA", default=0, type=int, help="Save data files?")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/output/birds_audio_tsne.csv", help="CSV output file")
args = parser.parse_args()

# Parse arguments
INPUT_FILES = args.INPUT_FILES
INPUT_AUDIO_DIR = args.INPUT_AUDIO_DIR
SAMPLES = args.SAMPLES
MIN_DUR = args.MIN_DUR
MAX_DUR = args.MAX_DUR
AMP_THESHOLD = args.AMP_THESHOLD
PLOT = args.PLOT > 0
SAVE_DATA = args.SAVE_DATA > 0
OUTPUT_FILE = args.OUTPUT_FILE

# Audio config
FFT = 2048
HOP_LEN = FFT/4

# Read files
files = []
if "*" in INPUT_FILES:
    files = glob.glob(INPUT_FILES)
elif ".json" in INPUT_FILES:
    with open(INPUT_FILES) as f:
        files = [INPUT_AUDIO_DIR % fn for fn in json.load(f)]
fileCount = len(files)
print("Found %s files" % fileCount)

# Make sure output dirs exist
outDirs = [os.path.dirname(OUTPUT_FILE)]
for outDir in outDirs:
    if not os.path.exists(outDir):
        os.makedirs(outDir)

def getFeatures(y, sr):
    # y = y[0:sr]  # analyze just first second
    S = librosa.feature.melspectrogram(y, sr=sr, n_mels=128)
    log_S = librosa.amplitude_to_db(S, ref=np.max)
    mfcc = librosa.feature.mfcc(S=log_S, n_mfcc=13)
    delta_mfcc = librosa.feature.delta(mfcc, mode='nearest')
    delta2_mfcc = librosa.feature.delta(mfcc, order=2, mode='nearest')
    # mode='nearest' can be added to avoid problems such as;
    #ParameterError: when mode='interp', width=9 cannot exceed data.shape[axis]=n
    feature_vector = np.concatenate((np.mean(mfcc,1), np.mean(delta_mfcc,1), np.mean(delta2_mfcc,1)))
    feature_vector = (feature_vector-np.mean(feature_vector))/np.std(feature_vector)
    return feature_vector

progress = 0
def doTSNE(fn):
    global progress
    global fileCount

    sampleData = []
    basename = os.path.splitext(os.path.basename(fn))[0]

    sampleData, ysamples, y, sr = getAudioSamples(fn, min_dur=MIN_DUR, max_dur=MAX_DUR, fft=FFT, hop_length=HOP_LEN, amp_threshold=AMP_THESHOLD)

    # if too many samples, take the ones with the most power
    if SAMPLES is not None and len(sampleData) > SAMPLES:
        sampleData = sorted(sampleData, key=lambda k: k['power'], reverse=True)
        sampleData = sampleData[:SAMPLES]

    featureData = []
    for d in sampleData:
        ysample = ysamples[d["index"]]
        featureVector = getFeatures(ysample, sr)
        featureData.append({
            "parent": basename,
            "note": d["note"],
            "start": d["start"],
            "dur": d["dur"],
            "featureVector": featureVector
        })

    progress += 1
    sys.stdout.write('\r')
    sys.stdout.write("%s%%" % round(1.0*progress/fileCount*100,1))
    sys.stdout.flush()

    return featureData

# for fn in files:
#     doTSNE(fn)
pool = ThreadPool()
data = pool.map(doTSNE, files)
pool.close()
pool.join()

data = [item for sublist in data for item in sublist]
featureVectors = [d["featureVector"] for d in data]
model = TSNE(n_components=2,
             learning_rate=150, # increase if too dense, decrease if too uniform
             verbose=1,
             angle=0.1 # increase to make faster, decrease to make more accurate
).fit_transform(featureVectors)

print("%s samples found." % len(featureVectors))
x = model[:,0]
y = model[:,1]

if PLOT:
    plt.figure(figsize = (10,10))
    # Highlight notes
    notes = list(set([d["note"] for d in data]))
    colors = [notes.index(d["note"]) for d in data]
    plt.scatter(x, y, c=colors)
    # Highlight unique files
    # parents = list(set([d["parent"] for d in data]))
    # colors = [parents.index(d["parent"]) for d in data]
    # plt.scatter(x, y, c=colors)
    # plt.scatter(x, y)
    plt.show()

# -*- coding: utf-8 -*-

# Looks for musical samples in arbitrary audio
# Adapted from: https://github.com/kylemcdonald/AudioNotebooks/blob/master/Multisamples%20to%20Samples.ipynb
# Usage:
    # python audio_to_samples.py -plot 1
    # python audio_to_samples.py -save 1
    # python audio_to_samples.py -in "../audio/downloads/birds/*.mp3"

import argparse
import csv
import glob
import librosa
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import os
from os.path import join
import numpy as np
from pprint import pprint
import sys
from utils import getAudioSamples

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILES", default="../audio/sample/*.mp3", help="Input file pattern")
parser.add_argument('-samples', dest="SAMPLES", default=8, type=int, help="Max samples to produce, -1 for all")
parser.add_argument('-min', dest="MIN_DUR", default=0.05, type=float, help="Minimum sample duration in seconds")
parser.add_argument('-max', dest="MAX_DUR", default=1.00, type=float, help="Maximum sample duration in seconds")
parser.add_argument('-amp', dest="AMP_THESHOLD", default=-1, type=float, help="Amplitude theshold, -1 for default")
parser.add_argument('-save', dest="SAVE", default=0, type=int, help="Save files?")
parser.add_argument('-plot', dest="PLOT", default=0, type=int, help="Show plot?")
parser.add_argument('-dir', dest="SAMPLE_DIR", default="../audio/output/birds", help="Output dir")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/output/birds_audio_samples.csv", help="CSV output file")
parser.add_argument('-overwrite', dest="OVERWRITE", default=0, type=int, help="Overwrite existing audio/data?")
args = parser.parse_args()

# Parse arguments
INPUT_FILES = args.INPUT_FILES
SAMPLES = args.SAMPLES
MIN_DUR = args.MIN_DUR
MAX_DUR = args.MAX_DUR
AMP_THESHOLD = args.AMP_THESHOLD
SAVE = args.SAVE > 0
PLOT = args.PLOT > 0
SAMPLE_DIR = args.SAMPLE_DIR
OUTPUT_FILE = args.OUTPUT_FILE
OVERWRITE = args.OVERWRITE > 0

if SAMPLES <= 0:
    SAMPLES = None

# Audio config
FFT = 2048
HOP_LEN = FFT/4

# Read files
files = glob.glob(INPUT_FILES)
fileCount = len(files)
print("Found %s files" % fileCount)

# Make sure output dirs exist
outDirs = [SAMPLE_DIR, os.path.dirname(OUTPUT_FILE)]
for outDir in outDirs:
    if not os.path.exists(outDir):
        os.makedirs(outDir)

progress = 0
# files = [files[2]]
def makeSamples(fn):
    global progress
    sampleData, ysamples, y, sr = getAudioSamples(fn, min_dur=MIN_DUR, max_dur=MAX_DUR, fft=FFT, hop_length=HOP_LEN, amp_threshold=AMP_THESHOLD, plot=PLOT)

    # if too many samples, take the ones with the most power
    if SAMPLES is not None and len(sampleData) > SAMPLES:
        sampleData = sorted(sampleData, key=lambda k: k['power'], reverse=True)
        sampleData = sampleData[:SAMPLES]

    if SAVE:
        for d in sampleData:
            ysample = ysamples[d["index"]]
            outFn = join(SAMPLE_DIR, d["filename"])
            if OVERWRITE or not os.path.isfile(outFn):
                sample = np.copy(ysample)
                sample /= np.abs(sample).max()
                librosa.output.write_wav(outFn, sample, sr)

    # sort chronologically
    sampleData = sorted(sampleData, key=lambda k: k['start'])

    progress += 1
    sys.stdout.write('\r')
    sys.stdout.write("%s%%" % round(1.0*progress/fileCount*100,1))
    sys.stdout.flush()

    return sampleData

pool = ThreadPool()
data = pool.map(makeSamples, files)
pool.close()
pool.join()

print("Writing data to file...")
headings = ["parent", "start", "dur", "power", "hz", "note", "octave"]
rowCount = 0
with open(OUTPUT_FILE, 'wb') as f:
    writer = csv.writer(f)
    writer.writerow(headings)
    for sdata in data:
        for entry in sdata:
            writer.writerow([entry[key] for key in headings])
            rowCount += 1
print("Wrote %s rows to %s" % (rowCount, OUTPUT_FILE))

# -*- coding: utf-8 -*-

# Looks for musical samples in arbitrary audio
# Adapted from: https://github.com/kylemcdonald/AudioNotebooks/blob/master/Multisamples%20to%20Samples.ipynb
# Usage:
    # python audio_to_phrases.py -plot 1
    # python audio_to_phrases.py -save 1
    # python audio_to_phrases.py -in "../audio/downloads/birds/*.mp3" -saved 1

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
from utils import getAudioSamples, getPhrases

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILES", default="../audio/sample/*.mp3", help="Input file pattern")
parser.add_argument('-min', dest="MIN_DUR", default=0.05, type=float, help="Minimum sample duration in seconds")
parser.add_argument('-max', dest="MAX_DUR", default=1.00, type=float, help="Maximum sample duration in seconds")
parser.add_argument('-minp', dest="MIN_PHRASE_DUR", default=0.5, type=float, help="Minimum phrase duration in seconds")
parser.add_argument('-maxp', dest="MAX_PHRASE_DUR", default=5.00, type=float, help="Maximum phrase duration in seconds")
parser.add_argument('-maxs', dest="MAX_SILENCE", default=0.25, type=float, help="Maximum silence between samples in phrase in seconds")
parser.add_argument('-amp', dest="AMP_THESHOLD", default=-1, type=float, help="Amplitude theshold, -1 for default")
parser.add_argument('-save', dest="SAVE", default=0, type=int, help="Save files?")
parser.add_argument('-saved', dest="SAVE_DATA", default=0, type=int, help="Save data files?")
parser.add_argument('-plot', dest="PLOT", default=0, type=int, help="Show plot?")
parser.add_argument('-dir', dest="SAMPLE_DIR", default="../audio/output/birds_phrases", help="Output dir")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/output/birds_audio_phrases.csv", help="CSV output file")
parser.add_argument('-overwrite', dest="OVERWRITE", default=0, type=int, help="Overwrite existing audio/data?")
args = parser.parse_args()

# Parse arguments
INPUT_FILES = args.INPUT_FILES
MIN_DUR = args.MIN_DUR
MAX_DUR = args.MAX_DUR
MIN_PHRASE_DUR = args.MIN_PHRASE_DUR
MAX_PHRASE_DUR = args.MAX_PHRASE_DUR
MAX_SILENCE = args.MAX_SILENCE
AMP_THESHOLD = args.AMP_THESHOLD
SAVE = args.SAVE > 0
SAVE_DATA = args.SAVE_DATA > 0
PLOT = args.PLOT > 0
SAMPLE_DIR = args.SAMPLE_DIR
OUTPUT_FILE = args.OUTPUT_FILE
OVERWRITE = args.OVERWRITE > 0

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

# files = [files[2]]
progress = 0
def makePhrases(fn):
    global progress
    # get sample data
    basename = os.path.splitext(os.path.basename(fn))[0]
    sampleData, ysamples, y, sr = getAudioSamples(fn, min_dur=MIN_DUR, max_dur=MAX_DUR, fft=FFT, hop_length=HOP_LEN, amp_threshold=AMP_THESHOLD, plot=PLOT)

    # get phrases from sample data
    phrases = getPhrases(sampleData, minLen=MIN_PHRASE_DUR, maxLen=MAX_PHRASE_DUR, maxSilence=MAX_SILENCE)
    # print "Found %s phrases in %s" % (len(phrases), basename)

    # add metadata
    for i, phrase in enumerate(phrases):
        phrases[i]["parent"] = basename
        phrases[i]["filename"] = "%s %s.wav" % (basename, phrase["start"])
        # stringify phrase
        rows = [[n["start"], n["dur"], n["power"], n["hz"], n["note"], n["octave"]] for n in phrase["phrase"]]
        phrases[i]["phrase"] = ",".join([":".join([str(col) for col in row]) for row in rows])

    if SAVE:
        for phrase in phrases:
            ysample = y[phrase["left"]*HOP_LEN:phrase["right"]*HOP_LEN]
            outFn = join(SAMPLE_DIR, phrase["filename"])
            if OVERWRITE or not os.path.isfile(outFn):
                sample = np.copy(ysample)
                sample /= np.abs(sample).max()
                librosa.output.write_wav(outFn, sample, sr)

    progress += 1
    sys.stdout.write('\r')
    sys.stdout.write("%s%%" % round(1.0*progress/fileCount*100,1))
    sys.stdout.flush()

    return phrases

# files = [files[1]]

pool = ThreadPool()
data = pool.map(makePhrases, files)
pool.close()
pool.join()

if SAVE_DATA:
    print("Writing data to file...")
    headings = ["parent", "start", "dur", "phrase"]
    rowCount = 0
    with open(OUTPUT_FILE, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(headings)
        for pdata in data:
            for entry in pdata:
                writer.writerow([entry[key] for key in headings])
                rowCount += 1
    print("Wrote %s rows to %s" % (rowCount, OUTPUT_FILE))

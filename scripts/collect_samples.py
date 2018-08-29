# -*- coding: utf-8 -*-

# Combines audio samples into single audio and manifest file
# Adapted from: https://github.com/kylemcdonald/AudioNotebooks/blob/master/Collect%20Samples.ipynb

import argparse
import glob
import os
from os.path import join
from pydub import AudioSegment
from pprint import pprint
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILES", default="../audio/output/birds/*.wav", help="Input file pattern")
parser.add_argument('-per', dest="SAMPLES_PER_FILE", default=100, type=int, help="Number of samples to combine into a single audio file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../audio/output/bird_collection_%s.mp3", help="Output file pattern")
parser.add_argument('-overwrite', dest="OVERWRITE", default=0, type=int, help="Overwrite existing audio/data?")
args = parser.parse_args()

# Parse arguments
INPUT_FILES = args.INPUT_FILES
SAMPLES_PER_FILE = args.SAMPLES_PER_FILE
OUTPUT_FILE = args.OUTPUT_FILE
OVERWRITE = args.OVERWRITE > 0

# Read files
files = glob.glob(INPUT_FILES)
fileCount = len(files)
print("Found %s files" % fileCount)

# Make sure output dirs exist
outDir = os.path.dirname(OUTPUT_FILE)
if not os.path.exists(outDir):
    os.makedirs(outDir)

i0 = 0
i1 = SAMPLES_PER_FILE

i = 1
while i0 < fileCount:
    i1 = min(i1, fileCount)
    samples = files[i0:i1]
    outFn = OUTPUT_FILE % str(i).zfill(2)

    if OVERWRITE or not os.path.isfile(outFn):
        print("Building %s..." % outFn)
        audio = AudioSegment.empty()

        for fn in samples:
            audio += AudioSegment.from_wav(fn)
        # audio /= audio.max # normalize

        # if MP3, write wav first, then convert to mp3 with ffmpeg
        format = outFn.split(".")[-1]
        file_handle = audio.export(outFn, format=format)

        print("Wrote %s to file" % outFn)

    i0 += SAMPLES_PER_FILE
    i1 += SAMPLES_PER_FILE
    i += 1

print "Done."

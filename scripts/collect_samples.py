# -*- coding: utf-8 -*-

# Combines audio samples into single audio and manifest file
# Adapted from: https://github.com/kylemcdonald/AudioNotebooks/blob/master/Collect%20Samples.ipynb

import argparse
import glob
import os
from os.path import join
import librosa
import numpy as np
from pprint import pprint
import subprocess
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILES", default="../audio/output/*.wav", help="Input file pattern")
parser.add_argument('-per', dest="SAMPLES_PER_FILE", default=100, type=int, help="Number of samples to combine into a single audio file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../audio/output/collection_%s.mp3", help="Output file pattern")
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

i0 = 0
i1 = SAMPLES_PER_FILE

i = 1
while i0 < fileCount:
    i1 = min(i1, fileCount)
    samples = files[i0:i1]
    outFn = OUTPUT_FILE % str(i).zfill(2)

    if OVERWRITE or not os.path.isfile(outFn):
        audio = np.array([])
        sr = 48000
        for fn in samples:
            # load audio
            y, sr = librosa.load(fn)
            audio = np.append(audio, y.reshape(-1))
        # audio = audio.reshape(-1)
        audio /= np.abs(audio).max() # normalize

        # if MP3, write wav first, then convert to mp3 with ffmpeg
        isMP3 = ".mp3" in outFn
        outWav = outFn
        if isMP3:
            outWav = outFn.replace(".mp3", ".wav")
        librosa.output.write_wav(outWav, audio, sr)

        if isMP3:
            command = ['ffmpeg',
                '-i', outWav,
                '-vn',
                '-ar', '44100',
                '-ac', '1', # mono vs stereo
                # '-ab', '192k',
                '-f', 'mp3',
                outFn]
            # print(" ".join(command))
            finished = subprocess.check_call(command)
            # remove temporary wav file
            os.remove(outWav)

        print("Write %s to file" % outFn)

    i0 += SAMPLES_PER_FILE
    i1 += SAMPLES_PER_FILE
    i += 1

print "Done."

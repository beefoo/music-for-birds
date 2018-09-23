# -*- coding: utf-8 -*-

import argparse
import glob
import math
import os
from pprint import pprint
from pydub import AudioSegment
import sys
from utils import writeMixFile

# input
parser = argparse.ArgumentParser()
parser.add_argument('-audio', dest="INPUT_AUDIO", default="../audio/output/birds/*.wav", help="Input audio file pattern")
parser.add_argument('-mode', dest="MODE", default="loop", help="Possible values: volume, pan, loop")
parser.add_argument('-dur', dest="DUR", default=120, type=int, help="Duration in seconds")
parser.add_argument('-beat', dest="BEAT", default=1000, type=int, help="Beat in ms")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/sample/mix.txt", help="Output file")
args = parser.parse_args()

INPUT_AUDIO = args.INPUT_AUDIO
MODE = args.MODE
DUR = args.DUR * 1000
BEAT = args.BEAT
OUTPUT_FILE = args.OUTPUT_FILE
MAX_SAMPLES = 100
PRECISION = 3

# Read files
files = glob.glob(INPUT_AUDIO)
fileCount = len(files)
print("Found %s files" % fileCount)

if fileCount > MAX_SAMPLES:
    print("Too many, reducing to %s samples" % MAX_SAMPLES)
    files = files[:MAX_SAMPLES]

if fileCount <= 0:
    print("No samples found")
    sys.exit(1)

instructions = []
beats = DUR / BEAT

if MODE == "volume":
    fn = files[0]
    basename = os.path.splitext(os.path.basename(fn))[0]
    phases = 5
    for i in range(beats):
        x = 1.0 * i / (beats-1)
        volume = 0.5*math.sin(x*phases*math.pi)+0.5
        volume = round(volume, PRECISION)
        instructions.append({
            "start": i * BEAT,
            "sound": basename,
            "volume": volume
        })

elif MODE == "pan":
    fn = files[0]
    basename = os.path.splitext(os.path.basename(fn))[0]
    phases = 5
    for i in range(beats):
        x = 1.0 * i / (beats-1)
        pan = math.sin(x*phases*math.pi)
        pan = round(pan, PRECISION)
        instructions.append({
            "start": i * BEAT,
            "sound": basename,
            "pan": pan
        })

elif MODE == "loop":
    samples = [os.path.splitext(os.path.basename(fn))[0] for fn in files]
    sampleCount = len(samples)
    counts = 16
    panPhases = 6
    volumePhases = 4
    offsetStep = BEAT / counts
    volumeMultiplier = 0.5
    for i in range(sampleCount):
        offset = i % counts * offsetStep
        xOffset = 1.0 * i / sampleCount
        for j in range(beats):
            x = 1.0 * j / (beats-1) + xOffset
            volume = 0.5*math.sin(x*volumePhases*math.pi)+0.5
            pan = math.sin(x*panPhases*math.pi)
            volume = round(volume, PRECISION)
            pan = round(pan, PRECISION)
            instructions.append({
                "start": j * BEAT + offset,
                "sound": samples[i],
                "volume": volume * volumeMultiplier,
                "pan": pan
            })

writeMixFile(OUTPUT_FILE, instructions)

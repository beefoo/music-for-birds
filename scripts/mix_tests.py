# -*- coding: utf-8 -*-

import argparse
import glob
import math
import os
from pprint import pprint
from pydub import AudioSegment
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-audio', dest="INPUT_AUDIO", default="../audio/output/birds/*.wav", help="Input audio file pattern")
parser.add_argument('-mode', dest="MODE", default="arch", help="Possible values: volume, pan, loop, arch")
parser.add_argument('-dur', dest="DUR", default=120, type=int, help="Duration in seconds")
parser.add_argument('-beat', dest="BEAT", default=500, type=int, help="Beat in ms")
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

samples = []
instructions = []
beats = DUR / BEAT

if MODE == "volume":
    fn = files[0]
    basename = os.path.basename(fn)
    samples.append(basename)
    phases = 5
    for i in range(beats):
        x = 1.0 * i / (beats-1)
        volume = 0.5*math.sin(x*phases*math.pi)+0.5
        volume = round(volume, PRECISION)
        instructions.append({
            "start": i * BEAT,
            "soundIndex": 0,
            "volume": volume,
            "pan": 0
        })

elif MODE == "pan":
    fn = files[0]
    basename = os.path.basename(fn)
    samples.append(basename)
    phases = 5
    for i in range(beats):
        x = 1.0 * i / (beats-1)
        pan = math.sin(x*phases*math.pi)
        pan = round(pan, PRECISION)
        instructions.append({
            "start": i * BEAT,
            "soundIndex": 0,
            "volume": 1.0,
            "pan": pan
        })

# build output file
lines = []
for sample in samples:
    lines.append(sample)
lines.append("---")
for i in instructions:
    row = [i["start"], i["soundIndex"], i["volume"], i["pan"]]
    row = [str(col) for col in row]
    line = ",".join(row)
    lines.append(line)
outString = "\n".join(lines)
with open(OUTPUT_FILE, 'w') as f:
    f.write(outString)
    print "Wrote %s instructions to %s" % (len(instructions), OUTPUT_FILE)

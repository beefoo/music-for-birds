# -*- coding: utf-8 -*-

import argparse
import csv
import os
from pprint import pprint
import sys
import time
from utils import readCsv, norm, writeMixFile

# input
parser = argparse.ArgumentParser()
parser.add_argument('-sample', dest="INPUT_SAMPLE_FILE", default="../data/output/birds_audio_samples.csv", help="Input samples csv file")
parser.add_argument('-sort', dest="SORT_BY", default="hz", help="Possible values: hz, power, dur")
parser.add_argument('-low', dest="MIN_VALUE", default=400.0, type=float, help="Possible values: hz, power, dur")
parser.add_argument('-high', dest="MAX_VALUE", default=2000.0, type=float, help="Possible values: hz, power, dur")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/output/bird_sort_hz_mix.txt", help="Output txt file")
args = parser.parse_args()

INPUT_SAMPLE_FILE = args.INPUT_SAMPLE_FILE
SORT_BY = args.SORT_BY
MIN_VALUE = args.MIN_VALUE
MAX_VALUE = args.MAX_VALUE
OUTPUT_FILE = args.OUTPUT_FILE
OVERLAP = 0.25

print("Reading data file...")
sampleData = readCsv(INPUT_SAMPLE_FILE)
print("Found %s rows in %s" % (len(sampleData), INPUT_SAMPLE_FILE))

# filter values
sampleData = [s for s in sampleData if MIN_VALUE <= s[SORT_BY] <= MAX_VALUE]

# sort values
sampleData = sorted(sampleData, key=lambda k: k[SORT_BY])
values = [s[SORT_BY] for s in sampleData]
print("%s range: [%s - %s]" % (SORT_BY, min(values), max(values)))

totalDur = sum([int(s["dur"]*(1.0-OVERLAP)) for s in sampleData])
print("Total time: %s" % time.strftime('%H:%M:%S', time.gmtime(totalDur/1000)))

instructions = []
start = 0
for s in sampleData:
    instructions.append({
        "start": start,
        "sound": s["parent"],
        "clipStart": s["start"],
        "clipDur": s["dur"]
    })
    start += int(s["dur"] * (1.0-OVERLAP)) # overlap the sounds a bit

writeMixFile(OUTPUT_FILE, parents, instructions)

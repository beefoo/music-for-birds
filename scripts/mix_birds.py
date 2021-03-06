# -*- coding: utf-8 -*-

import argparse
import csv
import math
import os
from pprint import pprint
import random
import sys
from utils import lerp, norm, readCsv, roundToNearest, writeMixFile

# input
parser = argparse.ArgumentParser()
parser.add_argument('-meta', dest="INPUT_META_FILE", default="../data/output/birds_audio_metadata.csv", help="Input metadata csv file")
parser.add_argument('-sample', dest="INPUT_SAMPLE_FILE", default="../data/output/birds_audio_samples.csv", help="Input samples csv file")
parser.add_argument('-phrase', dest="INPUT_PHRASE_FILE", default="../data/output/birds_audio_phrases.csv", help="Input phrase csv file")
parser.add_argument('-stat', dest="INPUT_PHRASE_STATS_FILE", default="../data/output/birds_audio_phrase_stats.csv", help="Input phrase stats csv file")
parser.add_argument('-chords', dest="INPUT_CHORDS_FILE", default="../data/mf18m_chords.csv", help="Input chords csv file")
parser.add_argument('-bpm', dest="BPM", default=120, type=int, help="Beats per minute")
parser.add_argument('-seeds', dest="SEEDS", default="2,2,2,2,2,2,2,2,2,2,2,2", help="List of seeds for pseudorandom number generation")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/output/bird_mix.txt", help="Output txt file")
args = parser.parse_args()

INPUT_META_FILE = args.INPUT_META_FILE
INPUT_SAMPLE_FILE = args.INPUT_SAMPLE_FILE
INPUT_PHRASE_FILE = args.INPUT_PHRASE_FILE
INPUT_PHRASE_STATS_FILE = args.INPUT_PHRASE_STATS_FILE
INPUT_CHORDS_FILE = args.INPUT_CHORDS_FILE
BPM = args.BPM
SEEDS = [int(s) for s in args.SEEDS.split(",")]
OUTPUT_FILE = args.OUTPUT_FILE

MS_PER_BEAT = int(round(60.0 / BPM * 1000))
DIVISIONS_PER_BEAT = 4 # e.g. 4 = quarter notes, 8 = eighth notes, etc
BEATS_PER_PHRASE = 16
ROUND_TO_NEAREST = int(round(MS_PER_BEAT/DIVISIONS_PER_BEAT))
VARIANCE_MS = 10 # +/- milliseconds an instrument note should be off by to give it a little more "natural" feel

seedPos = 0

print("Reading data file...")
metaData = readCsv(INPUT_META_FILE)
sampleData = readCsv(INPUT_SAMPLE_FILE)
phraseStats = readCsv(INPUT_PHRASE_STATS_FILE)
chordData = readCsv(INPUT_CHORDS_FILE)

# add note-octave to smapleData
for i, d in enumerate(sampleData):
    sampleData[i]["noteOctave"] = "%s%s" % (d["note"], d["octave"])
for i, d in enumerate(chordData):
    chordData[i]["noteOctave"] = "%s%s" % (d["note"], d["octave"])

print("Found %s rows in %s" % (len(metaData), INPUT_META_FILE))
print("Found %s rows in %s" % (len(sampleData), INPUT_SAMPLE_FILE))
print("Found %s rows in %s" % (len(phraseStats), INPUT_PHRASE_STATS_FILE))
print("Found %s rows in %s" % (len(chordData), INPUT_CHORDS_FILE))

# group chords
# chordValues = set([c["chord"] for c in chordData])
# chords = [[c for c in chordData if c["chord"]==v] for v in chordValues]

# get normalized values for power and duration
powerValues = [d["power"] for d in sampleData]
durValues = [d["dur"] for d in sampleData]
powerRange = (min(powerValues), max(powerValues))
durRange = (min(durValues), max(durValues))
for i, d in enumerate(sampleData):
    sampleData[i]["powerNorm"] = norm(d["power"], powerRange)
    sampleData[i]["durNorm"] = norm(d["dur"], durRange)

def getPhraseInstructions(sample, start, beats, ms_per_beat, volumeRange=(0.0, 1.0), tempoRange=(1.0, 1.0), panRange=(-1.0, 1.0), roundTo=1):
    ms = 0
    duration = beats * ms_per_beat
    instructions = []
    tempoFrom, tempoTo = tempoRange
    tempoRange = (int(round(ms_per_beat/tempoFrom)), int(round(ms_per_beat/tempoTo)))
    while ms < duration:
        pos = 1.0 * ms / duration
        pos = -(math.cos(math.pi*2.0*pos)-1) / 2.0 # sin curve in-out
        volume = lerp(volumeRange, pos)
        pan = lerp(panRange, pos)
        instructions.append({
            "sound": sample["parent"],
            "start": ms + start,
            "clipStart": sample["start"],
            "clipDur": sample["dur"],
            "volume": volume,
            "pan": pan
        })
        addMs = int(roundToNearest(lerp(tempoRange, pos), roundTo))
        addMs = max(addMs, roundTo)
        ms += addMs
    return instructions

# sort samples by frequency
sampleData = sorted(sampleData, key=lambda k: k["hz"])
maxMs = 3 * 60 * 1000

instructions = []
ms = 0
msStep = MS_PER_BEAT + MS_PER_BEAT / 2

for i, d in enumerate(sampleData):
    tempoRange = (1.0, 1.0)
    if d["durNorm"] >= 0.75 or d["powerNorm"] > 0.25:
        tempoRange = (0.5, 0.5)
    elif d["durNorm"] <= 0.25 and d["powerNorm"] < 0.5:
        tempoRange = (2.0, 2.0)
    volumeRange = (0.0, max(0.2, 1.0-d["powerNorm"]))
    panRange = (-1.0, 1.0) if i % 2 > 0 else (1.0, -1.0)
    instructions += getPhraseInstructions(d, ms, BEATS_PER_PHRASE, MS_PER_BEAT, volumeRange=volumeRange, tempoRange=tempoRange, panRange=panRange, roundTo=ROUND_TO_NEAREST)
    if (ms + BEATS_PER_PHRASE * MS_PER_BEAT) >= maxMs:
        break
    ms += msStep

writeMixFile(OUTPUT_FILE, instructions)

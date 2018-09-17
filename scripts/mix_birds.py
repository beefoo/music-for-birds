# -*- coding: utf-8 -*-

import argparse
import csv
import os
from pprint import pprint
import sys
from utils import readCsv, norm

# input
parser = argparse.ArgumentParser()
parser.add_argument('-meta', dest="INPUT_META_FILE", default="../data/output/birds_audio_metadata.csv", help="Input metadata csv file")
parser.add_argument('-sample', dest="INPUT_SAMPLE_FILE", default="../data/output/birds_audio_samples.csv", help="Input samples csv file")
parser.add_argument('-phrase', dest="INPUT_PHRASE_FILE", default="../data/output/birds_audio_phrases.csv", help="Input phrase csv file")
parser.add_argument('-stat', dest="INPUT_PHRASE_STATS_FILE", default="../data/output/birds_audio_phrase_stats.csv", help="Input phrase stats csv file")
parser.add_argument('-chords', dest="INPUT_CHORDS_FILE", default="../data/mf18m_chords.csv", help="Input chords csv file")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/output/bird_mix.txt", help="Output txt file")
args = parser.parse_args()

INPUT_META_FILE = args.INPUT_META_FILE
INPUT_SAMPLE_FILE = args.INPUT_SAMPLE_FILE
INPUT_PHRASE_FILE = args.INPUT_PHRASE_FILE
INPUT_PHRASE_STATS_FILE = args.INPUT_PHRASE_STATS_FILE
INPUT_CHORDS_FILE = args.INPUT_CHORDS_FILE
OUTPUT_FILE = args.OUTPUT_FILE

print("Reading data file...")
metaData = readCsv(INPUT_META_FILE)
sampleData = readCsv(INPUT_SAMPLE_FILE)
phraseStats = readCsv(INPUT_PHRASE_STATS_FILE)
chordData = readCsv(INPUT_CHORDS_FILE)

print("Found %s rows in %s" % (len(metaData), INPUT_META_FILE))
print("Found %s rows in %s" % (len(sampleData), INPUT_SAMPLE_FILE))
print("Found %s rows in %s" % (len(phraseStats), INPUT_PHRASE_STATS_FILE))
print("Found %s rows in %s" % (len(chordData), INPUT_CHORDS_FILE))

# get octave range
octaves = list(set([s["octave"] for s in sampleData]))
minOctave = min(octaves)
maxOctave = max(octaves)
octaves = list(set([c["octave"] for c in chordData]))
minChordOctave = min(octaves)
maxChordOctave = max(octaves)
print("Target octave range: %s - %s" % (minChordOctave, maxChordOctave))
print("Actual octave range: %s - %s" % (minOctave, maxOctave))

# filters
callSamples = [s for s in sampleData if "call" in s["parent"].lower()]

# group chords
chordValues = set([c["chord"] for c in chordData])
chords = [[c for c in chordData if c["chord"]==v] for v in chordValues]

instructions = []

for chord in chords:
    for note in chord:
        break
    break

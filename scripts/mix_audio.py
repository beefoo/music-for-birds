# -*- coding: utf-8 -*-

import argparse
import math
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import os
from pprint import pprint
from pydub import AudioSegment
import sys
from utils import volumeToDb

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="../data/sample/mix.txt", help="Input txt file")
parser.add_argument('-dir', dest="AUDIO_DIR", default="../audio/output/birds/", help="Input audio directory")
parser.add_argument('-left', dest="PAD_LEFT", default=2000, type=int, help="Pad left in milliseconds")
parser.add_argument('-right', dest="PAD_RIGHT", default=2000, type=int, help="Pad right in milliseconds")
parser.add_argument('-s0', dest="EXCERPT_START", default=-1, type=int, help="Slice start in ms")
parser.add_argument('-s1', dest="EXCERPT_END", default=-1, type=int, help="Slice end in ms")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../audio/output/sample_mix.wav", help="Output audio file")
args = parser.parse_args()

INPUT_FILE = args.INPUT_FILE
AUDIO_DIR = args.AUDIO_DIR
PAD_LEFT = args.PAD_LEFT
PAD_RIGHT = args.PAD_RIGHT
EXCERPT_START = args.EXCERPT_START
EXCERPT_END = args.EXCERPT_END
OUTPUT_FILE = args.OUTPUT_FILE

MIN_VOLUME = 0.01
MAX_VOLUME = 10.0

# Read input file
lines = [line.strip() for line in open(INPUT_FILE)]

# Retrieve sound files
soundFiles = []
instructionStartIndex = 0
for i, line in enumerate(lines):
    if line.startswith("---"):
        instructionStartIndex = i + 1
        break
    soundFiles.append(line)
sounds = [{"filename": AUDIO_DIR+fn} for fn in soundFiles]

# Retrieve instructions
instructions = []
for i, line in enumerate(lines):
    if i < instructionStartIndex:
        continue
    start, soundIndex, volume, pan = tuple(line.split(","))

    # parse volume
    volume = float(volume)
    if volume < MIN_VOLUME:
        continue
    volume = min(volume, MAX_VOLUME)
    db = volumeToDb(volume)

    instructions.append({
        "start": int(start) + PAD_LEFT,
        "soundIndex": int(soundIndex),
        "db": db,
        "pan": float(pan)
    })

# Make excerpt
if EXCERPT_START > 0:
    instructions = [i for i in instructions if i["start"] > (EXCERPT_START-PAD_LEFT)]
if EXCERPT_END > 0:
    instructions = [i for i in instructions if i["start"] < (EXCERPT_END-PAD_LEFT)]
soundIndices = list(set([i["soundIndex"] for i in instructions]))

# Load sounds
print("Loading sounds...")
for i, sound in enumerate(sounds):
    sounds[i]["index"] = i
    # Don't load sound if we don't have to
    if i not in soundIndices:
        continue
    segment = AudioSegment.from_file(sound["filename"], format="wav")
    # convert to stereo
    if segment.channels != 2:
        segment = segment.set_channels(2)
    sounds[i]["audio"] = segment

print("Loaded %s sounds" % len(sounds))

instructions = sorted(instructions, key=lambda k: k['start'])
INSTRUCTION_COUNT = len(instructions)

if INSTRUCTION_COUNT <= 0 or len(sounds) <= 0:
    print("No instructions or sounds")
    sys.exit(1)

# determine duration
last = instructions[-1]
duration = last["start"] + len(sounds[last["soundIndex"]]) + PAD_RIGHT
frame_rate = sounds[0]["audio"].frame_rate
print("Creating audio file with duration %ss" % round(duration/1000.0, 3))

progress = 0
def makeTrack(p):
    global progress

    duration = p["duration"]
    frame_rate = p["frame_rate"]
    instructions = p["instructions"]
    sound = p["sound"]

    # build audio
    baseAudio = AudioSegment.silent(duration=duration, frame_rate=frame_rate)
    baseAudio = baseAudio.set_channels(2)
    for index, i in enumerate(instructions):
        newSound = sound["audio"]
        if i["db"] != 0.0:
            newSound = newSound.apply_gain(i["db"])
        if i["pan"] != 0.0:
            newSound = newSound.pan(i["pan"])
        baseAudio = baseAudio.overlay(newSound, position=i["start"])

        progress += 1
        sys.stdout.write('\r')
        sys.stdout.write("%s%%" % round(1.0*progress/INSTRUCTION_COUNT*100,1))
        sys.stdout.flush()

    return baseAudio

# Build track parameters
trackParams = [{
    "duration": duration,
    "frame_rate": frame_rate,
    "instructions": [i for i in instructions if i["soundIndex"]==s["index"]],
    "sound": s
} for s in sounds]

print("Building %s tracks..." % len(trackParams))
pool = ThreadPool()
tracks = pool.map(makeTrack, trackParams)
pool.close()
pool.join()

print("Combining tracks...")
baseAudio = AudioSegment.silent(duration=duration, frame_rate=frame_rate)
for track in tracks:
    baseAudio = baseAudio.overlay(track)

print("Writing to file...")
format = OUTPUT_FILE.split(".")[-1]
f = baseAudio.export(OUTPUT_FILE, format=format)
print("Wrote to %s" % OUTPUT_FILE)

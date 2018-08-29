import argparse
import math
import os
from pprint import pprint
from pydub import AudioSegment
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="../data/sample/mix.txt", help="Input txt file")
parser.add_argument('-dir', dest="AUDIO_DIR", default="../audio/output/birds/", help="Input audio directory")
parser.add_argument('-left', dest="PAD_LEFT", default=2000, type=int, help="Pad left in milliseconds")
parser.add_argument('-right', dest="PAD_RIGHT", default=2000, type=int, help="Pad right in milliseconds")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/output/sample_mix.wav", help="Output csv file pattern")
args = parser.parse_args()

INPUT_FILE = args.INPUT_FILE
AUDIO_DIR = args.AUDIO_DIR
PAD_LEFT = args.PAD_LEFT
PAD_RIGHT = args.PAD_RIGHT
OUTPUT_FILE = args.OUTPUT_FILE

# Read input file
lines = [line.strip() for line in INPUT_FILE]

# Retrieve sound files
soundFiles = []
instructionStartIndex = 0
for i, line in enumerate(lines):
    if line.startswith("---"):
        instructionStartIndex = i + 1
        break
    soundFiles.append(line)
sounds = [{"filename": AUDIO_DIR+fn} for fn in soundFiles]

# Load sounds
print("Loading sounds...")
for i, sound in enumerate(sounds):
    sounds[i]["audio"] = AudioSegment.from_file(sound["filename"], format="wav")
print("Loaded %s sounds" % len(sounds))

def volumeToDb(volume):
    db = 0.0
    if volume < 1.0 || volume > 1.0:
        # half volume = −6db = 10*log(0.5*0.5)
        db = 10.0 * math.log(volume**2)
    return db

# Retrieve instructions
instructions = []
for i, line in enumerate(lines):
    if i < instructionStartIndex:
        continue
    start, soundIndex, volume, pan = tuple(line.split(","))
    db = volumeToDb(volume)
    instructions.append({
        "start": int(start),
        "soundIndex": int(soundIndex),
        "db": db,
        "pan": float(pan)
    })
instructions = sorted(instructions, key=lambda k: k['start'])

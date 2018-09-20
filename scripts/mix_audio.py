# -*- coding: utf-8 -*-

# python -W ignore mix_audio.py -in ../data/output/bird_sort_hz_mix.txt -dir ../audio/downloads/birds/%s.mp3 -out ../audio/output/bird_sort_hz_mix.mp3 -reverb 50

import argparse
import math
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import os
from pprint import pprint
from pydub import AudioSegment
import sys
from utils import addReverb, volumeToDb

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="../data/sample/mix.txt", help="Input txt file")
parser.add_argument('-dir', dest="AUDIO_DIR", default="../audio/output/birds/%s.wav", help="Input audio directory")
parser.add_argument('-left', dest="PAD_LEFT", default=3000, type=int, help="Pad left in milliseconds")
parser.add_argument('-right', dest="PAD_RIGHT", default=3000, type=int, help="Pad right in milliseconds")
parser.add_argument('-s0', dest="EXCERPT_START", default=-1, type=int, help="Slice start in ms")
parser.add_argument('-s1', dest="EXCERPT_END", default=-1, type=int, help="Slice end in ms")
parser.add_argument('-reverb', dest="REVERB", default=75, type=int, help="Add reverb (0-100)")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../audio/output/sample_mix.mp3", help="Output audio file")
args = parser.parse_args()

INPUT_FILE = args.INPUT_FILE
AUDIO_DIR = args.AUDIO_DIR
PAD_LEFT = args.PAD_LEFT
PAD_RIGHT = args.PAD_RIGHT
EXCERPT_START = args.EXCERPT_START
EXCERPT_END = args.EXCERPT_END
REVERB = args.REVERB
OUTPUT_FILE = args.OUTPUT_FILE

MIN_VOLUME = 0.01
MAX_VOLUME = 10.0
CLIP_FADE_IN_DUR = 100
CLIP_FADE_OUT_DUR = 100
REVERB_PAD = 3000
SAMPLE_WIDTH = 2

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
sounds = [{"filename": AUDIO_DIR % fn} for fn in soundFiles]

# Retrieve instructions
instructions = []
for i, line in enumerate(lines):
    if i < instructionStartIndex:
        continue
    start, soundIndex, clipStart, clipDur, volume, pan, fadeIn, fadeOut = tuple(line.split(","))

    # parse volume
    volume = float(volume)
    if volume < MIN_VOLUME:
        continue
    volume = min(volume, MAX_VOLUME)
    db = volumeToDb(volume)

    instructions.append({
        "start": int(start) + PAD_LEFT,
        "soundIndex": int(soundIndex),
        "clipStart": int(clipStart),
        "clipDur": int(clipDur),
        "db": db,
        "pan": float(pan),
        "fadeIn": int(fadeIn),
        "fadeOut": int(fadeOut)
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
    fformat = sound["filename"].split(".")[-1].lower()
    segment = AudioSegment.from_file(sound["filename"], format=fformat)
    # convert to stereo
    if segment.channels != 2:
        segment = segment.set_channels(2)
    # convert sample width
    if segment.sample_width != SAMPLE_WIDTH:
        segment = segment.set_sample_width(SAMPLE_WIDTH)

    # look through instructions to find unique clips
    clips = [(ii["clipStart"], ii["clipDur"]) for ii in instructions if ii["soundIndex"]==i]
    clips = list(set(clips))

    # make segments from clips
    segments = []
    for clipStart, clipDur in clips:
        clipEnd = None
        if clipDur > 0:
            clipEnd = clipStart + clipDur
        clip = segment[clipStart:clipEnd]
        if clipEnd is None:
            clip = segment[clipStart:]

        # add a fade in/out to avoid clicking
        fadeInDur = CLIP_FADE_IN_DUR if clipDur <= 0 else min(CLIP_FADE_IN_DUR, clipDur)
        fadeOutDur = CLIP_FADE_OUT_DUR if clipDur <= 0 else min(CLIP_FADE_OUT_DUR, clipDur)
        clip = clip.fade_in(fadeInDur).fade_out(fadeOutDur)

        # add reverb
        if REVERB > 0:
            # pad clip to accommodate reverb
            clip += AudioSegment.silent(duration=REVERB_PAD, frame_rate=clip.frame_rate)
            clip = addReverb(clip, reverberance=REVERB)

        segments.append({
            "id": (clipStart, clipDur),
            "start": clipStart,
            "dur": clipDur,
            "sound": clip
        })
    sounds[i]["segments"] = segments

print("Loaded %s sounds" % len(sounds))

instructions = sorted(instructions, key=lambda k: k['start'])
INSTRUCTION_COUNT = len(instructions)

if INSTRUCTION_COUNT <= 0 or len(sounds) <= 0:
    print("No instructions or sounds")
    sys.exit(1)

# determine duration
last = instructions[-1]
duration = last["start"] + len(sounds[last["soundIndex"]]) + PAD_RIGHT
frame_rate = sounds[0]["segments"][0]["sound"].frame_rate
print("Creating audio file with duration %ss" % round(duration/1000.0, 3))

progress = 0
def makeTrack(p):
    global progress

    duration = p["duration"]
    frame_rate = p["frame_rate"]
    instructions = p["instructions"]
    sound = p["sound"]
    segments = sound["segments"]

    # build audio
    baseAudio = AudioSegment.silent(duration=duration, frame_rate=frame_rate)
    baseAudio = baseAudio.set_channels(2)
    for index, i in enumerate(instructions):
        segment = [s for s in segments if s["id"]==(i["clipStart"], i["clipDur"])].pop()
        sound = segment["sound"]

        if i["db"] != 0.0:
            sound = sound.apply_gain(i["db"])
        if i["pan"] != 0.0:
            sound = sound.pan(i["pan"])
        if i["fadeIn"] > 0:
            sound = sound.fade_in(i["fadeIn"])
        if i["fadeOut"] > 0:
            sound = sound.fade_out(i["fadeOut"])
        baseAudio = baseAudio.overlay(sound, position=i["start"])

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
# for p in trackParams:
#     tracks.append(makeTrack(p))

print("Combining tracks...")
baseAudio = AudioSegment.silent(duration=duration, frame_rate=frame_rate)
for track in tracks:
    baseAudio = baseAudio.overlay(track)

print("Writing to file...")
format = OUTPUT_FILE.split(".")[-1]
f = baseAudio.export(OUTPUT_FILE, format=format)
print("Wrote to %s" % OUTPUT_FILE)

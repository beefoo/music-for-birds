# -*- coding: utf-8 -*-

import argparse
import glob
from lib import *
import math
from mutagen.mp3 import MP3
import os
from pprint import pprint
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILES", default="../audio/downloads/*.mp3", help="Input file pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/audio_metadata.csv", help="CSV output file")

args = parser.parse_args()

INPUT_FILES = args.INPUT_FILES
OUTPUT_FILE = args.OUTPUT_FILE

files = glob.glob(INPUT_FILES)
print("Found %s files" % len(files))

for f in files:
    audio = MP3(f)
    # print(audio.tags.pprint())
    length = audio.info.length

    # parse comments
    comments = str(audio.tags["COMM::ENG"])

    # parse groups
    group = str(audio.tags["TIT1"])
    group = group.replace(", and ", ", ")
    group = group.replace(" and ", ", ")

    pprint([length, comments, group])
    break

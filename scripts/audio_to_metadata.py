# -*- coding: utf-8 -*-

import argparse
import glob
import math
from mutagen.mp3 import MP3
import os
from pprint import pprint
import re
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILES", default="../audio/sample/*.mp3", help="Input file pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/audio_metadata.csv", help="CSV output file")

args = parser.parse_args()

INPUT_FILES = args.INPUT_FILES
OUTPUT_FILE = args.OUTPUT_FILE

files = glob.glob(INPUT_FILES)
print("Found %s files" % len(files))

metadata = []
for f in files:
    fname = os.path.basename(f)
    basename = fname.split('.')[0]

    audio = MP3(f)
    # print(audio.tags.pprint())
    length = audio.info.length

    # parse filename for metadata
    name = ""
    sampleNumber = 0
    description = ""
    matches = re.match("([A-Z].+) ([0-9]+) ([A-Z].+)", basename)
    if matches:
        name = matches.group(1)
        sampleNumber = int(matches.group(2))
        description = matches.group(3)

    # parse comments for metadata
    comments = [c.strip() for c in str(audio.tags["COMM::ENG"]).split(";")]
    clen = len(comments)
    species = "" if clen <= 0 else comments[0]
    place = "" if clen <= 1 else comments[1]
    authors = "" if clen <= 2 else [c.strip() for c in comments[2].split(",")]
    uid = "" if clen <= 3 else comments[3]

    # parse groups
    groups = str(audio.tags["TIT1"])
    groups = groups.replace(", and ", ", ")
    groups = groups.replace(" and ", ", ")
    groups = [g.strip() for g in groups.split(",")]

    entry = {
        "filename": fname,
        "length": length,
        "name": name,
        "sample": sampleNumber,
        "description": description,
        "species": species,
        "place": place,
        "authors": authors,
        "uid": uid,
        "groups": groups
    }
    metadata.append(entry)
    # print(entry)
    # print "---"

# -*- coding: utf-8 -*-

# Usage: python audio_to_metadata.py -in "../audio/downloads/*.mp3"

import argparse
import csv
import glob
import math
from mutagen.mp3 import MP3
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import librosa
import os
from pprint import pprint
import re
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILES", default="../audio/sample/*.mp3", help="Input file pattern")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/output/audio_metadata.csv", help="CSV output file")

args = parser.parse_args()

INPUT_FILES = args.INPUT_FILES
OUTPUT_FILE = args.OUTPUT_FILE

files = glob.glob(INPUT_FILES)
fileCount = len(files)
print("Found %s files" % fileCount)
progress = 0

def readFile(f):
    global progress
    fname = os.path.basename(f)
    basename = fname.split('.')[0]

    # use librosa to get duration
    y, sr = librosa.load(f)
    duration = round(librosa.get_duration(y=y, sr=sr), 3)

    audio = MP3(f)

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
    comments = []
    if "COMM::ENG" in audio.tags:
        comments = [c.strip() for c in str(audio.tags["COMM::ENG"]).split(";")]
    clen = len(comments)
    species = "" if clen <= 0 else comments[0]
    place = ["", ""] if clen <= 1 else  [c.strip() for c in comments[1].split(",")]
    authors = [] if clen <= 2 else [c.strip() for c in comments[2].split(",")]
    uid = "" if clen <= 3 else comments[3]

    # parse place
    state = ""
    country = ""
    if len(place) == 2:
        state, country = tuple(place)
    elif len(place) == 1:
        country = place[0]

    # parse groups
    groups = []
    if "TIT1" in audio.tags:
        groups = str(audio.tags["TIT1"])
        groups = groups.replace(", and ", ", ")
        groups = groups.replace(" and ", ", ")
        groups = [g.strip() for g in groups.split(",")]

    entry = {
        "filename": basename,
        "duration": duration,
        "name": name,
        "sample": sampleNumber,
        "description": description,
        "species": species,
        "state": state,
        "country": country,
        "authors": ", ".join(authors),
        "uid": uid,
        "groups": ", ".join(groups)
    }
    # print(entry)
    # print("---")
    progress += 1
    sys.stdout.write('\r')
    sys.stdout.write("%s%%" % round(1.0*progress/fileCount*100,1))
    sys.stdout.flush()
    return entry

pool = ThreadPool()
metadata = pool.map(readFile, files)
pool.close()
pool.join()

print("Writing data to file...")
headings = ["filename", "uid", "name", "species", "description", "groups", "sample", "duration", "state", "country", "authors"]
with open(OUTPUT_FILE, 'wb') as f:
    writer = csv.writer(f)
    writer.writerow(headings)
    for entry in metadata:
        writer.writerow([entry[key] for key in headings])

print("Wrote %s rows to %s" % (fileCount, OUTPUT_FILE))

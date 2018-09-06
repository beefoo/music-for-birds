# -*- coding: utf-8 -*-

# Usage: python audio_to_metadata.py -in "../audio/downloads/birds/*.mp3"

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
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/output/birds_audio_metadata.csv", help="CSV output file")

args = parser.parse_args()

INPUT_FILES = args.INPUT_FILES
OUTPUT_FILE = args.OUTPUT_FILE

files = glob.glob(INPUT_FILES)
fileCount = len(files)
print("Found %s files" % fileCount)
progress = 0

# Make sure output dirs exist
outDir = os.path.dirname(OUTPUT_FILE)
if not os.path.exists(outDir):
    os.makedirs(outDir)

def isDateStr(str):
    return re.match("[0-9]+ [A-Z][a-z]+ [0-9]{4}", str)

def isUid(str):
    return re.match("ML [0-9]+", str)

def isAuthor(str):
    return ("." in str or "Sharon" in str or "Richard" in str)

def readFile(f):
    global progress
    fname = os.path.basename(f)
    basename = fname.split('.')[0]

    # use librosa to get duration
    duration = round(librosa.get_duration(filename=f), 3)

    audio = MP3(f)

    # parse filename for metadata
    name = ""
    sampleNumber = 0
    placecode = ""
    description = ""
    matches = re.match("([A-Z].+) ([0-9]+) ([A-Z]+?) ([A-Z0-9].+)", basename)
    if matches:
        name = matches.group(1)
        sampleNumber = int(matches.group(2))
        placecode = matches.group(3)
        description = matches.group(4)
    else:
        matches = re.match("([A-Z].+) ([0-9]+) ([A-Z0-9].+)", basename)
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
    place = ["", ""]
    date = ""
    authors = []
    uid = ""

    # e.g. Maine, United States; Gregory F. Budney
    if clen == 2:
        species = ""
        place = [c.strip() for c in comments[0].split(",")]
        authors = [c.strip() for c in comments[1].split(",")]
    # e.g. Agelaius phoeniceus; Richard W. Simmers; ML 12354
    elif clen == 3:
        c1 = comments[1]
        if isDateStr(c1):
            date = c1
        elif isAuthor(c1):
            authors =  [c.strip() for c in c1.split(",")]
        else:
            place = [c.strip() for c in c1.split(",")]
        uid = comments[2]
    # e.g. Anous stolidus; 21 April 1985; Edward H. Miller; ML 117673
    elif clen == 4:
        c1 = comments[1]
        if isDateStr(c1):
            date = c1
        else:
            place = [c.strip() for c in c1.split(",")]
        authors =  [c.strip() for c in comments[2].split(",")]
        uid = comments[3]
    # standard case, e.g. Agelaius phoeniceus; Maryland, United States; 27 February 1998; Wilbur L. Hershberger; ML 94215
    elif clen == 5:
        place = [c.strip() for c in comments[1].split(",")]
        date = comments[2]
        authors =  [c.strip() for c in comments[3].split(",")]
        uid = comments[4]

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
        "placecode": placecode,
        "authors": ", ".join(authors),
        "date": date,
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

# files = files[:100]

pool = ThreadPool()
metadata = pool.map(readFile, files)
pool.close()
pool.join()

print("Writing data to file...")
headings = ["filename", "uid", "name", "species", "description", "groups", "sample", "duration", "state", "country", "placecode", "date", "authors"]
with open(OUTPUT_FILE, 'wb') as f:
    writer = csv.writer(f)
    writer.writerow(headings)
    for entry in metadata:
        writer.writerow([entry[key] for key in headings])

print("Wrote %s rows to %s" % (fileCount, OUTPUT_FILE))

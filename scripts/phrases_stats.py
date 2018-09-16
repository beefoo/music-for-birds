# -*- coding: utf-8 -*-

# Usage: python phrases_stats.py -min 5 -mind 1200 -out "../data/output/birds_audio_phrase_stats_ui.csv" -rowh 4 -draw 1
#        python phrases_stats.py -min 3 -mind 800 -out "../data/output/birds_audio_phrase_stats_query.csv"

import argparse
import csv
import numpy as np
import os
from pprint import pprint
import sys
from utils import readCsv, norm

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="../data/output/birds_audio_phrases.csv", help="Input csv file")
parser.add_argument('-img', dest="IMAGE_FILE", default="../data/output/birds_audio_phrases.png", help="Output image file")
parser.add_argument('-width', dest="IMAGE_WIDTH", default=800, type=int, help="Width of image")
parser.add_argument('-rowh', dest="ROW_HEIGHT", default=10, type=int, help="Height of image row")
parser.add_argument('-draw', dest="DRAW_IMAGE", default=0, type=int, help="Should draw image?")
parser.add_argument('-min', dest="MIN_NOTES_PER_PHRASE", default=2, type=int, help="Minimum amounts of notes to be considered a phrase")
parser.add_argument('-mind', dest="MIN_DURATION", default=500, type=int, help="Minimum duration of phrase in ms")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/output/birds_audio_phrase_stats.csv", help="Output csv file")
args = parser.parse_args()

INPUT_FILE = args.INPUT_FILE
IMAGE_FILE = args.IMAGE_FILE
IMAGE_WIDTH = args.IMAGE_WIDTH
ROW_HEIGHT = args.ROW_HEIGHT
DRAW_IMAGE = args.DRAW_IMAGE > 0
MIN_NOTES_PER_PHRASE = args.MIN_NOTES_PER_PHRASE
MIN_DURATION = args.MIN_DURATION
OUTPUT_FILE = args.OUTPUT_FILE

COLORS = {
    "A": (120, 28, 129),
    "G#": (70, 41, 135),
    "E": (63, 89, 169),
    "G": (70, 134, 194),
    "C": (88, 164, 172),
    "A#": (115, 181, 128),
    "F#": (149, 189, 94),
    "F": (185, 189, 74),
    "B": (214, 177, 62),
    "D#": (229, 146, 53),
    "D": (229, 94, 43),
    "C#": (217, 33, 32)
}

print("Reading data file...")
data = readCsv(INPUT_FILE)
rowCount = len(data)
print("Found %s rows in %s" % (rowCount, INPUT_FILE))

# entry keys: parent,start,dur,phrase
# phrase keys: start,dur,power,hz,note,octave

for i, entry in enumerate(data):
    phrase = [v.split(":") for v in entry["phrase"].split(",")]
    for j, v in enumerate(phrase):
        phrase[j] = {
            "start": int(v[0]),
            "dur": int(v[1]),
            "power": float(v[2]),
            "hz": float(v[3]),
            "note": v[4],
            "octave": int(v[5]),
        }
    data[i]["phrase"] = phrase

# remove invalid phrases
data = [d for d in data if d["dur"] >= MIN_DURATION and len(d["phrase"]) >= MIN_NOTES_PER_PHRASE]
rowCount = len(data)
print("Found %s valid rows in %s" % (rowCount, INPUT_FILE))

# calculate standard deviations for frequency and rhythms
for i, entry in enumerate(data):
    hzs = []
    durs = []
    pows = []
    deltas = []
    phrase = entry["phrase"]
    for j, note in enumerate(phrase):
        hzs.append(note["hz"])
        durs.append(note["dur"])
        pows.append(note["power"])
        if j > 0:
            deltas.append(note["start"]-phrase[j-1]["start"])
    data[i]["count"] = len(phrase)
    data[i]["hzMean"] = int(round(np.mean(hzs)))
    data[i]["durMean"] = int(round(np.mean(durs)))
    data[i]["powMean"] = round(np.mean(pows), 1)
    data[i]["hzStd"] = int(round(np.std(hzs)))
    data[i]["beatStd"] = int(round((np.std(durs) + np.std(deltas)) * 0.5))
    data[i]["notes"] = "".join(list(set([n["note"] for n in phrase])))

maxDur = max([d["dur"] for d in data])
print("Max duration is %sms" % maxDur)

if DRAW_IMAGE:
    from PIL import Image, ImageDraw

    IMAGE_HEIGHT = ROW_HEIGHT * rowCount
    print("Creating %s x %s image" % (IMAGE_WIDTH, IMAGE_HEIGHT))
    im = Image.new(mode="RGB", size=(IMAGE_WIDTH, IMAGE_HEIGHT), color="white")

    draw = ImageDraw.Draw(im)
    for i, entry in enumerate(data):
        y0 = i * ROW_HEIGHT
        y1 = (i+1) * ROW_HEIGHT
        start = entry["start"]
        end = entry["start"]+entry["dur"]
        width = 1.0 * entry["dur"] / maxDur * IMAGE_WIDTH
        for note in entry["phrase"]:
            color = COLORS[note["note"]]
            x0 = norm(note["start"], start, end) * width
            x1 = norm(note["start"]+note["dur"], start, end) * width
            draw.rectangle([x0, y0, x1, y1], fill=color, outline="white")
        sys.stdout.write('\r')
        sys.stdout.write("%s%%" % round(1.0*(i+1)/rowCount*100,1))
        sys.stdout.flush()
    del draw

    # write to stdout
    im.save(IMAGE_FILE, "PNG")
    print("Wrote %s" % IMAGE_FILE)

headings = ["parent", "start", "dur", "count", "hzMean", "durMean", "powMean", "hzStd", "beatStd", "notes"]
with open(OUTPUT_FILE, 'wb') as f:
    writer = csv.writer(f)
    writer.writerow(headings)
    rows = []
    for entry in data:
        row = []
        for key in headings:
            row.append(entry[key])
        rows.append(row)
    writer.writerows(rows)
    print "Wrote %s rows to %s" % (len(rows), OUTPUT_FILE)

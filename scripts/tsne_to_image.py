# -*- coding: utf-8 -*-

import argparse
import csv
import os
from PIL import Image, ImageDraw
from pprint import pprint
import random
import sys
from utils import readCsv

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="../data/output/birds_audio_tsne.csv", help="Input csv file")
parser.add_argument('-width', dest="WIDTH", default=8000, type=int, help="Target width")
parser.add_argument('-height', dest="HEIGHT", default=8000, type=int, help="Target height")
parser.add_argument('-rad', dest="RADIUS", default=4, type=int, help="Radius of each audio clip")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/output/birds_audio_tsne.png", help="Output file")
args = parser.parse_args()

# Parse arguments
INPUT_FILE = args.INPUT_FILE
WIDTH = args.WIDTH
HEIGHT = args.HEIGHT
RADIUS = args.RADIUS
OUTPUT_FILE = args.OUTPUT_FILE

colors = [
    (120, 28, 129),
    (70, 41, 135),
    (63, 89, 169),
    (70, 134, 194),
    (88, 164, 172),
    (115, 181, 128),
    (149, 189, 94),
    (185, 189, 74),
    (214, 177, 62),
    (229, 146, 53),
    (229, 94, 43),
    (217, 33, 32)
]
random.seed(3)
random.shuffle(colors)
colorCount = len(colors)

# Read files
print("Reading data file...")
data = readCsv(INPUT_FILE)
rowCount = len(data)
print("Found %s rows in %s" % (rowCount, INPUT_FILE))

groups = list(set(d["group"] for d in data))

# Make sure output dirs exist
outDirs = [os.path.dirname(OUTPUT_FILE)]
for outDir in outDirs:
    if not os.path.exists(outDir):
        os.makedirs(outDir)

im = Image.new(mode="RGB", size=(WIDTH, HEIGHT), color=(0, 0, 0))

draw = ImageDraw.Draw(im)
for i, d in enumerate(data):
    x0 = d["x"] * WIDTH
    y0 = d["y"] * HEIGHT
    x1 = x0 + RADIUS * 2
    y1 = y0 + RADIUS * 2
    color = colors[groups.index(d["group"]) % colorCount]
    draw.ellipse([x0, y0, x1, y1], fill=color)
    sys.stdout.write('\r')
    sys.stdout.write("%s%%" % round(1.0*(i+1)/rowCount*100,1))
    sys.stdout.flush()
del draw

# write to stdout
print "Writing image to file..."
im.save(OUTPUT_FILE, "PNG")
print("Wrote %s" % OUTPUT_FILE)

# -*- coding: utf-8 -*-

import argparse
import csv
import os
from PIL import Image, ImageDraw
from pprint import pprint
import sys
from utils import readCsv

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILE", default="../data/output/birds_phrases_tsne.csv", help="Input csv file")
parser.add_argument('-width', dest="WIDTH", default=8000, type=int, help="Target width")
parser.add_argument('-height', dest="HEIGHT", default=8000, type=int, help="Target height")
parser.add_argument('-rad', dest="RADIUS", default=4, type=int, help="Radius of each audio clip")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/output/birds_phrases_tsne.png", help="Output file")
args = parser.parse_args()

# Parse arguments
INPUT_FILE = args.INPUT_FILE
WIDTH = args.WIDTH
HEIGHT = args.HEIGHT
RADIUS = args.RADIUS
OUTPUT_FILE = args.OUTPUT_FILE

# Read files
print("Reading data file...")
data = readCsv(INPUT_FILE)
rowCount = len(data)
print("Found %s rows in %s" % (rowCount, INPUT_FILE))

# Make sure output dirs exist
outDirs = [os.path.dirname(OUTPUT_FILE)]
for outDir in outDirs:
    if not os.path.exists(outDir):
        os.makedirs(outDir)

im = Image.new(mode="RGBA", size=(WIDTH, HEIGHT), color=(255,255,255,0))

draw = ImageDraw.Draw(im)
for i, d in enumerate(data):
    x0 = d["x"] * WIDTH
    y0 = d["y"] * HEIGHT
    x1 = x0 + RADIUS * 2
    y1 = y0 + RADIUS * 2
    draw.ellipse([x0, y0, x1, y1], fill=(71, 156, 198, 128), outline="white")
    sys.stdout.write('\r')
    sys.stdout.write("%s%%" % round(1.0*(i+1)/rowCount*100,1))
    sys.stdout.flush()
del draw

# write to stdout
im.save(OUTPUT_FILE, "PNG")
print("Wrote %s" % OUTPUT_FILE)

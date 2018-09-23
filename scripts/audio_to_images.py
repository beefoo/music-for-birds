# -*- coding: utf-8 -*-

# Looks for musical samples in arbitrary audio
# Adapted from: https://github.com/kylemcdonald/AudioNotebooks/blob/master/Multisamples%20to%20Samples.ipynb
# Usage:
    # python audio_to_images.py -plot 1
    # python audio_to_images.py -save 1
    # python audio_to_images.py -in "../data/usergen/saved_birds.json"

import argparse
import csv
import glob
import json
import librosa
from librosa import display
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import os
from os.path import join
import numpy as np
from pprint import pprint
import sys

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILES", default="../data/usergen/saved_birds.json", help="Input file pattern")
parser.add_argument('-dir', dest="INPUT_AUDIO_DIR", default="../audio/downloads/birds/%s.mp3", help="Input audio directory")
parser.add_argument('-save', dest="SAVE", default=0, type=int, help="Save files?")
parser.add_argument('-plot', dest="PLOT", default=0, type=int, help="Show plot?")
parser.add_argument('-width', dest="WIDTH", default=3600, type=int, help="Target width")
parser.add_argument('-height', dest="HEIGHT", default=600, type=int, help="Target height")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/output/images/%s.png", help="Output file pattern")
parser.add_argument('-overwrite', dest="OVERWRITE", default=0, type=int, help="Overwrite existing images?")
args = parser.parse_args()

# Parse arguments
INPUT_FILES = args.INPUT_FILES
INPUT_AUDIO_DIR = args.INPUT_AUDIO_DIR
SAVE = args.SAVE > 0
PLOT = args.PLOT > 0
OUTPUT_FILE = args.OUTPUT_FILE
OVERWRITE = args.OVERWRITE > 0

# Audio config
FFT = 2048
HOP_LEN = FFT/4

# Read files
files = []
if "*" in INPUT_FILES:
    files = glob.glob(INPUT_FILES)
elif ".json" in INPUT_FILES:
    with open(INPUT_FILES) as f:
        files = [INPUT_AUDIO_DIR % fn for fn in json.load(f)]

fileCount = len(files)
print("Found %s files" % fileCount)

# Make sure output dirs exist
outDirs = [os.path.dirname(OUTPUT_FILE)]
for outDir in outDirs:
    if not os.path.exists(outDir):
        os.makedirs(outDir)

progress = 0
# files = files[:1]

def makeImage(fn):
    global progress
    basename = basename = os.path.splitext(os.path.basename(fn))[0]
    fileout = OUTPUT_FILE % basename
    w = 24
    h = 8

    y, sr = librosa.load(fn)
    D = librosa.amplitude_to_db(np.abs(librosa.stft(y)), ref=np.max)

    figure = plt.figure(figsize=(3600, 600), dpi=1)
    librosa.display.specshow(D, y_axis='log')

    if PLOT:
        plt.show()

    if SAVE and (OVERWRITE or not os.path.isfile(fileout)):
        axis = plt.subplot(1, 1, 1)
        plt.axis('off')
        plt.tick_params(axis='both', left='off', top='off', right='off', bottom='off', labelleft='off', labeltop='off', labelright='off', labelbottom='off')
        extent = axis.get_window_extent().transformed(figure.dpi_scale_trans.inverted())
        pts = extent.get_points()
        pad = 3.5
        pts[0][0] += pad
        pts[0][1] += pad
        pts[1][0] -= pad
        pts[1][1] -= pad
        extent.set_points(pts)
        plt.savefig(fileout, bbox_inches=extent, pad_inches=0)
        # print("Saved %s" % fileout)
    plt.cla()
    plt.clf()
    plt.close()

    progress += 1
    sys.stdout.write('\r')
    sys.stdout.write("%s%%" % round(1.0*progress/fileCount*100,1))
    sys.stdout.flush()

    return fileout

# pool = ThreadPool()
# data = pool.map(makeImage, files)
# pool.close()
# pool.join()
for fn in files:
    makeImage(fn)

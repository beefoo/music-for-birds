# -*- coding: utf-8 -*-

# Adapted from: https://github.com/kylemcdonald/AudioNotebooks/blob/master/Multisamples%20to%20Samples.ipynb

import argparse
import glob
from matplotlib import pyplot as plt
from matplotlib import patches
import os
from os.path import join
import librosa
from librosa import display
import numpy as np
from pprint import pprint
import sys
from utils import weighted_mean

# input
parser = argparse.ArgumentParser()
parser.add_argument('-in', dest="INPUT_FILES", default="../audio/sample/*.mp3", help="Input file pattern")
parser.add_argument('-samples', dest="SAMPLES", default=8, type=int, help="Max samples to produce, -1 for all")
parser.add_argument('-min', dest="MIN_DUR", default=0.05, type=float, help="Minimum sample duration in seconds")
parser.add_argument('-max', dest="MAX_DUR", default=1.00, type=float, help="Maximum sample duration in seconds")
parser.add_argument('-amp', dest="AMP_THESHOLD", default=-1, type=float, help="Amplitude theshold, -1 for default")
parser.add_argument('-save', dest="SAVE", default=0, type=int, help="Save files?")
parser.add_argument('-plot', dest="PLOT", default=0, type=int, help="Show plot?")
parser.add_argument('-dir', dest="SAMPLE_DIR", default="../audio/output", help="Output dir")
parser.add_argument('-out', dest="OUTPUT_FILE", default="../data/audio_samples.csv", help="CSV output file")
parser.add_argument('-overwrite', dest="OVERWRITE", default=0, type=int, help="Overwrite existing audio/data?")
args = parser.parse_args()

# Parse arguments
INPUT_FILES = args.INPUT_FILES
SAMPLES = args.SAMPLES
MIN_DUR = args.MIN_DUR
MAX_DUR = args.MAX_DUR
AMP_THESHOLD = args.AMP_THESHOLD
SAVE = args.SAVE > 0
PLOT = args.PLOT > 0
SAMPLE_DIR = args.SAMPLE_DIR
OUTPUT_FILE = args.OUTPUT_FILE
OVERWRITE = args.OVERWRITE > 0

if SAMPLES <= 0:
    SAMPLES = None

# Audio config
FFT = 2048
HOP_LEN = FFT/4
PLOT_DOWNSAMPLE = 100
FIGSIZE = (30,3)

# Read files
files = glob.glob(INPUT_FILES)
print("Found %s files" % len(files))

def getSlices(e, ampMin, minLen, maxLen):
    stdev = np.std(e)
    minAmp = min(stdev * 1.5, 0.5)
    if ampMin >= 0:
        minAmp = ampMin
    slices = []
    prev = None
    start = None
    end = None
    for i, value in enumerate(e):
        # first
        if prev is None:
            prev = value
            continue
        # we've hit the beginning of a slice
        if prev < minAmp and value >= minAmp:
            start = i
        # we've hit the end of a slice
        elif prev >= minAmp and value < minAmp:
            end = i
        # add slice
        if start is not None and end is not None:
            if end > start:
                slices.append([start, end])
            start = None
            end = None
        prev = value

    maxIndex = len(e) - 1
    # backtrack and look ahead
    for i, slice in enumerate(slices):
        left, right = tuple(slice)
        # backtrack left
        value = e[left]
        j = left - 1
        while j >= 0:
            vnew = e[j]
            if vnew < value:
                value = vnew
            else:
                break
            j -= 1
        leftNew = max(j + 1, 0)
        # look ahead right
        value = e[right]
        j = right + 1
        while j <= maxIndex:
            vnew = e[j]
            if vnew < value:
                value = vnew
            else:
                break
            j += 1
        rightNew = min(j - 1, maxIndex)
        # update slice
        slices[i] = [leftNew, rightNew]

    # remove slices that are too long or too short
    slices = [s for s in slices if s[1]-s[0] >= minLen and s[1]-s[0] <= maxLen]

    return slices

# files = [files[2]]

for fn in files:
    basename = os.path.basename(fn).split('.')[0]

    # load audio
    y, sr = librosa.load(fn)
    y /= y.max()
    ylen = len(y)
    duration = ylen/sr

    min_duration_frames = librosa.core.time_to_frames([MIN_DUR], sr=sr, hop_length=HOP_LEN)[0]
    max_duration_frames = librosa.core.time_to_frames([MAX_DUR], sr=sr, hop_length=HOP_LEN)[0]
    print("%s / %s seconds" % (basename, round(duration, 2)))

    # if PLOT:
    #     # plot the raw waveform
    #     plt.figure(figsize=FIGSIZE)
    #     plt.plot(y[::PLOT_DOWNSAMPLE])
    #     plt.xlim([0, ylen/PLOT_DOWNSAMPLE])
    #     plt.gca().xaxis.set_visible(False)
    #     plt.gca().yaxis.set_visible(False)
    #     # plt.show()

    # compute the rmse (root-mean-square energy) and threshold at a fixed value
    S = librosa.stft(y, n_fft=FFT, hop_length=HOP_LEN)
    e = librosa.feature.rmse(S=S)[0]
    e -= e.min()
    e /= e.max()

    slices = getSlices(e, AMP_THESHOLD, min_duration_frames, max_duration_frames)

    if PLOT:
        # plot the rmse and thresholded rmse
        plt.figure(figsize=FIGSIZE)
        plt.plot(e)
        # plt.show()

    sliceCount = len(slices)
    print(" -> Found %s samples" % sliceCount)
    sampleData = []
    ysamples = []
    i = 0
    for left, right in slices:
        if PLOT:
            # highlight saved chunks
            fillcolor = "blue" if i % 2 > 0 else "red"
            plt.gca().add_patch(patches.Rectangle((left, 0), (right - left), 1, alpha=0.2, color=fillcolor))

        ysample = y[left*HOP_LEN:right*HOP_LEN]
        stft = librosa.feature.rmse(S=librosa.stft(ysample, n_fft=FFT, hop_length=HOP_LEN))[0]
        rolloff = librosa.feature.spectral_rolloff(y=ysample, sr=sr)[0]
        # notes = [librosa.hz_to_note(hz) for hz in rolloff]
        # pprint(notes)
        start = round(1.0 * (left*HOP_LEN) / ylen, 5)
        end =  round(1.0 * (right*HOP_LEN) / ylen, 5)
        dur = int(round((end - start) * duration * 1000))
        power = round(weighted_mean(stft), 2)
        hz = round(weighted_mean(rolloff), 2)
        note = librosa.hz_to_note(hz)
        startms = int(round(start * duration * 1000))
        sampleFilename = "%s %s.wav" % (basename, startms)

        ysamples.append(ysample)
        sampleData.append({
            "index": i,
            "parent": basename,
            "filename": sampleFilename,
            "start": start,
            "dur": dur,
            "power": power,
            "hz": hz,
            "note": note
        })
        i+=1
        # print("pos=%s, dur=%s, hz=%s (%s) power=%s" % (start, dur, hz, note, power))

    # if too many samples, take the ones with the most power
    if SAMPLES is not None and len(sampleData) > SAMPLES:
        sampleData = sorted(sampleData, key=lambda k: k['power'], reverse=True)
        sampleData = sampleData[:SAMPLES]

    if SAVE:
        for d in sampleData:
            ysample = ysamples[d["index"]]
            outFn = join(SAMPLE_DIR, d["filename"])
            if OVERWRITE or not os.path.isfile(outFn):
                sample = np.copy(ysample)
                sample /= np.abs(sample).max()
                librosa.output.write_wav(outFn, sample, sr)

    if PLOT:
        # finish up the plot we've been building
        plt.xlim([0, len(e)])
        plt.gca().xaxis.set_visible(False)
        plt.gca().yaxis.set_visible(False)
        plt.show()

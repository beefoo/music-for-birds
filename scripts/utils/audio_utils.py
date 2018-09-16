# -*- coding: utf-8 -*-

import array
import librosa
from librosa import display
import math
from math_utils import weighted_mean
from matplotlib import pyplot as plt
from matplotlib import patches
import numpy as np
import os
from pprint import pprint
from pydub import AudioSegment
from pysndfx import AudioEffectsChain
import re
import sys

def addReverb(sound, reverberance=50):
    # convert pydub sound to np array
    samples = np.array(sound.get_array_of_samples())
    samples = samples.astype(np.int16)

    # apply reverb effect
    fx = (
        AudioEffectsChain()
        .reverb(reverberance=reverberance)
    )
    y = fx(samples)

    # convert it back to an array and create a new sound clip
    newData = array.array(sound.array_type, y)
    newSound = sound._spawn(newData)
    return newSound

def getAudioSamples(fn, min_dur=0.05, max_dur=0.75, fft=2048, hop_length=512, amp_threshold=-1, plot=False, plotfilename="../data/output/plot.png"):
    basename = os.path.basename(fn).split('.')[0]

    # load audio
    y, sr = librosa.load(fn)
    y /= y.max()
    ylen = len(y)
    duration = ylen/sr

    min_duration_frames = librosa.core.time_to_frames([min_dur], sr=sr, hop_length=hop_length)[0]
    max_duration_frames = librosa.core.time_to_frames([max_dur], sr=sr, hop_length=hop_length)[0]

    # compute the rmse (root-mean-square energy) and threshold at a fixed value
    S = librosa.stft(y, n_fft=fft, hop_length=hop_length)
    e = librosa.feature.rmse(S=S)[0]
    e -= e.min()
    e /= e.max()

    slices = getSlices(e, amp_threshold, min_duration_frames, max_duration_frames)
    sliceCount = len(slices)
    # print("Found %s samples in %s" % (sliceCount, basename))
    sampleData = []
    ysamples = []
    i = 0
    for left, right in slices:
        ysample = y[left*hop_length:right*hop_length]
        stft = librosa.feature.rmse(S=librosa.stft(ysample, n_fft=fft, hop_length=hop_length))[0]
        rolloff = librosa.feature.spectral_rolloff(y=ysample, sr=sr)[0]
        # notes = [librosa.hz_to_note(hz) for hz in rolloff]
        # pprint(notes)
        start = round(1.0 * (left*hop_length) / ylen, 5)
        end =  round(1.0 * (right*hop_length) / ylen, 5)
        dur = int(round((end - start) * duration * 1000))
        power = round(weighted_mean(stft), 2)
        hz = round(weighted_mean(rolloff), 2)
        note = librosa.hz_to_note(hz)
        startms = int(round(start * duration * 1000))
        sampleFilename = "%s %s.wav" % (basename, startms)

        # parse note
        octave = -1
        matches = re.match("([A-Z]\#?b?)(\-?[0-9]+)", note)
        if matches:
            note = matches.group(1)
            octave = int(matches.group(2))

        ysamples.append(ysample)
        sampleData.append({
            "index": i,
            "parent": basename,
            "filename": sampleFilename,
            "start": startms,
            "dur": dur,
            "power": power,
            "hz": hz,
            "note": note,
            "octave": octave,
            "left": left,
            "right": right
        })
        i+=1
        # print("pos=%s, dur=%s, hz=%s (%s) power=%s" % (start, dur, hz, note, power))

    if plot:
        showAudioPlot(y, e, slices, filename=plotfilename)

    return (sampleData, ysamples, y, sr)

def getPhrases(sampleData, minLen, maxLen, maxSilence, minNotesPerPhrase=2):
    # conver to ms
    minLen *= 1000
    maxLen *= 1000
    maxSilence *= 1000
    # build phrases
    phrases = []
    currentPhrase = []
    prevMs = None
    for s in sampleData:
        start = s["start"]
        if prevMs is not None and (start-prevMs) > maxSilence:
            phrases.append({ "phrase": currentPhrase[:] })
            currentPhrase = []
        else:
            currentPhrase.append(s)
        prevMs = start + s["dur"]
    phrases.append({ "phrase": currentPhrase[:] })

    # remove phrases with too little notes
    phrases = [p for p in phrases if len(p["phrase"]) >= minNotesPerPhrase]

    # add metadata
    for i, p in enumerate(phrases):
        phrase = p["phrase"]
        first = phrase[0]
        last = phrase[-1]
        phrases[i]["start"] = first["start"]
        phrases[i]["dur"] = (last["start"]+last["dur"])-first["start"]
        phrases[i]["left"] = first["left"]
        phrases[i]["right"] = last["right"]

    # remove phrases too long or short
    phrases = [p for p in phrases if minLen <= p["dur"] <= maxLen]

    return phrases

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

def showAudioPlot(y, e, slices, filename="output_plot.png", figsize=(30,3), downsample=100):
    # # plot the raw waveform
    # plt.figure(figsize=figsize)
    # plt.plot(y[::downsample])
    # plt.xlim([0, len(y)/downsample])
    # plt.gca().xaxis.set_visible(False)
    # plt.gca().yaxis.set_visible(False)
    # # plt.show()

    # plot the rmse and thresholded rmse
    plt.figure(figsize=figsize)
    plt.plot(e)

    # highlight samples
    i = 0
    for left, right in slices:
        fillcolor = "blue" if i % 2 > 0 else "red"
        plt.gca().add_patch(patches.Rectangle((left, 0), (right - left), 1, alpha=0.2, color=fillcolor))
        i += 1

    plt.xlim([0, len(e)])
    plt.gca().xaxis.set_visible(False)
    plt.gca().yaxis.set_visible(False)

    # plt.show()
    plt.tight_layout()
    plt.savefig(filename, bbox_inches="tight", pad_inches=0)
    plt.close()

def volumeToDb(volume):
    db = 0.0
    if volume < 1.0 or volume > 1.0:
        # half volume = −6db = 10*log(0.5*0.5)
        db = 10.0 * math.log(volume**2)
    return db

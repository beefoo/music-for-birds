# -*- coding: utf-8 -*-

# Wrapper for SOX: http://sox.sourceforge.net/sox.html#EFFECTS

import array
import librosa
import numpy as np
from pydub import AudioSegment
from pysndfx import AudioEffectsChain

infile = '../audio/downloads/birds/Boreal Owl 1 AK Male primary or staccato song.mp3'
clipStart = 9596
clipDur = 1288
clipPadding = 3000
fadeDur = 100
clipEnd = clipStart + clipDur
outfile = '../audio/output/sfxtest.mp3'

reverbTests = [
    (50, 50, 100),
    (75, 50, 100),
    (75, 50, 100),
    (75, 50, 100)
]

# Read and clip the sound
sound = AudioSegment.from_file(infile, format="mp3")
frame_rate = sound.frame_rate
clip = sound[clipStart:clipEnd]
clip = clip.fade_out(fadeDur)

# Add padding to clip and get the sample data as np array
padding = AudioSegment.silent(duration=clipPadding)
clip = clip + padding
# samples = np.right_shift(clip.get_array_of_samples(), 1)
samples = np.array(clip.get_array_of_samples())
samples = samples.astype(np.int16)

# build a base audio file
totalDuration = (clipDur + clipPadding) * len(reverbTests) * 2
print("Creating audio file %s seconds long" % round(totalDuration/1000, 2))
baseAudio = AudioSegment.silent(duration=totalDuration, frame_rate=frame_rate)

# go through each reverb test and add to base audio
pos = 0
for test in reverbTests:
    # Add the original audio clip
    baseAudio = baseAudio.overlay(clip, pos)
    pos += clipDur + clipPadding

    # build reverb effect
    reverberance, hf_damping, room_scale = test
    fx = (
        AudioEffectsChain()
        .reverb(reverberance=reverberance, hf_damping=hf_damping, room_scale=room_scale)
    )
    # apply effect to np array of samples
    y = np.copy(samples)
    y = fx(y)
    # y /= np.abs(y).max()

    # convert it back to an array and create a new sound clip
    newData = array.array(clip.array_type, y)
    newClip = clip._spawn(newData)

    # add new clip to audio
    baseAudio = baseAudio.overlay(newClip, pos)
    pos += clipDur + clipPadding

baseAudio.export(outfile, format="mp3")
print("Wrote result to %s" % outfile)

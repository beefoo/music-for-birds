# https://github.com/yuma-m/synthesizer
from synthesizer import Synthesizer, Waveform, Writer

writer = Writer()
synthesizer = Synthesizer(osc1_waveform=Waveform.sine, osc1_volume=1.0, use_osc2=False)

chord = [261.626, 329.628, 391.996]
writer.write_wave("../audio/output/synthtest.wav", synthesizer.generate_chord(chord, 5.0))

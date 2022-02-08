# plinkykeeb_sampleplayer.py - play multiple samples concurrently, some looped, some not
#
# 5 Feb 2022 - @todbot / Tod Kurt - https://github.com/todbot/plinkykeeb
#
# Convert files to appropriate WAV format (mono, 22050 Hz, 16-bit signed) with command:
#  sox loop.mp3 -b 16 -c 1 -r 22050 loop.wav
# or try:
#  ffmpeg -i loop.mp3 -ac 1 -ar 22050 loop.wav  (but I think this needs codec spec'd
#

print("plinkykeeb_sampleplayer!")

import time
import board
import keypad

import audiocore
import audiomixer
from audiopwmio import PWMAudioOut as AudioOut


# map key number to wave file
# a list of which samples to play on which keys,
# and if the sample should loop or not
wav_files = (
    # filename,           loop?
    ('wav/909kick4b.wav', False),       # C
    (None,None),                        # C#
    ('wav/909snare2b.wav', False),      # D
    (None, None),                       # D#
    (None, None),                       # E
    (None, None),                       # F
    ('wav/909hatclosed2b.wav', False),  # F#
    (None, None),                       # G
    ('wav/909hatopen5b.wav', False),    # G#
    (None, None),                       # A
    (None, None),                       # A#
    (None, None),                       # B
    ('wav/amenfull_22k_s16.wav', True), # C#
    ('wav/ohohoh.wav', False),          # D
    (None, None),                       # D#
    (None, None),                       # E
)

# pins used by keyboard
row_pins = (board.D7, board.D8, board.D9, board.D10)
col_pins = (board.D2, board.D3, board.D4, board.D5, board.D6)

km = keypad.KeyMatrix( row_pins=row_pins, column_pins=col_pins )

# audio pin is RX (pin 1)
audio = AudioOut(board.RX)
mixer = audiomixer.Mixer(voice_count=len(wav_files), sample_rate=22050, channel_count=1,
                         bits_per_sample=16, samples_signed=True)
# attach mixer to audio playback
audio.play(mixer)

# play or stop a sample using the mixer
def handle_sample(num, pressed):
    voice = mixer.voice[num]   # get mixer voice
    (wav_file, loopit) = wav_files[num]
    if pressed:
        if wav_file is not None:
            wave = audiocore.WaveFile(open(wav_file,"rb")) 
            voice.play(wave,loop=loopit)
    else: # released
        if loopit:
            voice.stop()  # only stop looping samples, others one-shot

 
while True:
    event = km.events.get()
    if event:
        print("key:%d %d/%d %d" % (event.key_number, event.pressed, event.released, event.timestamp) )
        
        if event.pressed:
            handle_sample( event.key_number, True )

        if event.released:
            handle_sample( event.key_number, False )
        

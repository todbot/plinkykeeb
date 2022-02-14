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
import neopixel
import rainbowio

import audiocore
import audiomixer
from audiopwmio import PWMAudioOut as AudioOut

# map key number to wave file
# a list of which samples to play on which keys,
# and if the sample should loop or not
# if a key has no sample, use (None,None)
wav_files = (
    # filename,           loop?
    ('wav/909kick4.wav', False),        # C
    ('wav/909clap1.wav', False),        # C#
    ('wav/909snare2.wav', False),       # D
    ('wav/909cym2.wav', False),         # D#
    (None, None),                       # E
    (None, None),                       # F
    ('wav/909hatclosed2.wav', False),   # F#
    (None, None),                       # G
    ('wav/909hatopen5.wav', False),     # G#
    (None, None),                       # A
    (None, None),                       # A#
    (None, None),                       # B
    ('wav/amenfull_22k_s16.wav', True), # C
    ('wav/amen1_22k_s16.wav', True),    # C#
    ('wav/ohohoh2.wav', True),          # D
    ('wav/amen2_22k_s16.wav', True),    # D#
    (None, None),                       # E
)

leds = neopixel.NeoPixel(board.MISO, 20, brightness=0.2, auto_write=False)

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

# # load all the wavs into RAM
# wavs = [None] * len(wav_files)
# for i in range(len(wavs)):
#     (wav_file, loopit) = wav_files[i]
#     if wav_file is not None:
#         wavs[i] = audiocore.WaveFile(open(wav_file,"rb"))

# # play or stop a RAM WAV sample using the mixer
# def handle_sample_wavs(num, pressed):
#     voice = mixer.voice[num]   # get mixer voice
#     (wav_file, loopit) = wav_files[num]
#     if pressed:
#         if wav_file is not None:
#             voice.play(wavs[num],loop=loopit)
#     else: # released
#         if loopit:
#             voice.stop()  # only stop looping samples, others one-shot

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


# I like millis
def millis(): return time.monotonic()*1000

# scale a value by amount/256, expects an int, returns an int
def scale8(val,amount):
    return (val*amount)//256
# dim all leds by an (amount/256)
def dim_leds_by(leds, amount):
    leds[0:] = [[max(scale8(i,amount),0) for i in l] for l in leds]

leds.fill(0x333333)

led_last_update_millis = 0
led_millis = 5

keys_pressed = []  # list of keys currently being pressed down
while True:
    now = millis()
    
    # update the LEDs, but only if keys pressed
    if now - led_last_update_millis > led_millis:
        led_last_update_millis = now
        for i in keys_pressed:  # light up those keys that are pressed
            leds[ i ] = rainbowio.colorwheel( int(time.monotonic() * 20) )
        dim_leds_by(leds, 250)  # fade everyone out slowly
        leds.show()
    
    event = km.events.get()
    
    if event:
        print("key:%d %d/%d %d" % (event.key_number, event.pressed, event.released, event.timestamp) )

        if event.key_number < len(wav_files):
            if event.pressed:
                handle_sample( event.key_number, True )
                keys_pressed.append( event.key_number )

            if event.released:
                handle_sample( event.key_number, False )
                keys_pressed.remove( event.key_number )
        

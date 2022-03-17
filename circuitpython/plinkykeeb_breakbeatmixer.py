# plinkykeeb_breakbeatmixer.py -- use CircuitPython mixer level to remix amen break
# 16 Mar 2022 - @todbot / Tod Kurt, from @jedgarparks' idea
#
# Uses pin defs from plinkykeeb but will work on other RP2040 CircuitPython boards
#
import time
import board
import keypad
import busio
import neopixel
import rainbowio

import audiocore
import audiomixer
from audiopwmio import PWMAudioOut as AudioOut

time.sleep(3)

wav_files = (
    'wav/amen_4bar_22k16b.wav', # 137.72 bpm
    'wav/amen_bitA_22k16b.wav',
    'wav/amen_bitB_22k16b.wav',
    'wav/amen_bitC_22k16b.wav',
    'wav/amen_bitD_22k16b.wav',
    'wav/amen_bitE_22k16b.wav',
    'wav/amen_bitF_22k16b.wav',
)
num_voices = len(wav_files)

leds = neopixel.NeoPixel(board.MISO, 20, brightness=0.2, auto_write=True)

row_pins = (board.D7, board.D8, board.D9, board.D10)
col_pins = (board.D2, board.D3, board.D4, board.D5, board.D6)

km = keypad.KeyMatrix( row_pins=row_pins, column_pins=col_pins )

audio = AudioOut( board.RX )
mixer = audiomixer.Mixer(voice_count=num_voices, sample_rate=22050, channel_count=1,
                         bits_per_sample=16, samples_signed=True)
audio.play(mixer) # attach mixer to audio playback

for i in range(num_voices):  # test start all samples at once for use w handle_mixer
    print("loading wav:", wav_files[i])
    wave = audiocore.WaveFile(open(wav_files[i],"rb"))
    mixer.voice[i].play(wave, loop=True)
    mixer.voice[i].level = 0

def handle_mixer(num, pressed):
    voice = mixer.voice[num]   # get mixer voice
    if pressed:
        voice.level = 1.0
    else: # released
        voice.level = 0

print("running")

while True:
    leds.fill( rainbowio.colorwheel( int(time.monotonic() * 20) ) )
    
    event = km.events.get()

    if event:
        print("key:%d %d/%d %d" % (event.key_number, event.pressed, event.released, event.timestamp) )

        if event.key_number < num_voices:
            if event.pressed:
                handle_mixer(event.key_number, True)
            if event.released:
                handle_mixer( event.key_number, False )



######################3

import time
import math
import array
import board
import keypad
import busio
import neopixel
import rainbowio

import audiocore
import audiomixer
from audiopwmio import PWMAudioOut as AudioOut

time.sleep(3)

num_voices = 24

leds = neopixel.NeoPixel(board.MISO, 20, brightness=0.2, auto_write=False)

row_pins = (board.D7, board.D8, board.D9, board.D10)
col_pins = (board.D2, board.D3, board.D4, board.D5, board.D6)

km = keypad.KeyMatrix( row_pins=row_pins, column_pins=col_pins )

audio = AudioOut( board.RX )
mixer = audiomixer.Mixer(voice_count=num_voices, sample_rate=22050, channel_count=1,
                         bits_per_sample=16, samples_signed=False)
audio.play(mixer) # attach mixer to audio playback

freqs = (
                                                65.4064,    69.2957,   73.4162,    77.7817,
    82.4069,   87.3071,   92.4986,   97.9989,   103.8262,   110.0000,  116.5409,   123.4708,
    130.8128,  138.5913,  146.8324,  155.5635,  164.8138,   174.6141,  184.9972,   195.9977,
    207.6523,  220.0000,  233.0819,  246.9417,  261.6256,   277.1826,  293.6648,   311.1270,
    329.6276,  349.2282,  369.9944,  391.9954,  415.3047,   440.0000,
)

tone_volume = 0.5
frequency = 440  # Set this to the Hz of the tone you want to generate.
length = 22050 // frequency
sine_wave = array.array("H", [0] * length)

for i in range(length):
    sine_wave[i] = int((1 + math.sin(math.pi * 2 * i / length)) * tone_volume * (2 ** 15 - 1))

sine_wave_sample = audiocore.RawSample(sine_wave, sample_rate=22050)

#mixer.voice[0].play(sine_wave_sample, loop=True)

def millis(): return time.monotonic()*1000

print("ready!")

decaying = False

while True:
    now = millis()

    if decaying:
        l = mixer.voice[0].level
        if l == 0:
            decaying = False
        else:
            mixer.voice[0].level = max(l - 0.001, 0)

    while km.events:
        event = km.events.get()
        print("key:%d %d/%d %d" % (event.key_number, event.pressed, event.released, event.timestamp) )
        if event.pressed:
            pass
        if event.released:
            pass
        
    # event = km.events.get()
    # if event:
    #     print("key:%d %d/%d %d" % (event.key_number, event.pressed, event.released, event.timestamp) )
    #     if event.pressed:
    #         #mixer.voice[ 0 ].level = 1.0
    #     if event.released:
    #         decaying = True
    #         #mixer.voice[ 0 ].level = 0.0







# plinkykeeb_midiout.py - send MIDI out via USB or serial
#
# 4 Feb 2022 - @todbot / Tod Kurt - https://github.com/todbot/plinkykeeb
#

print("plinkykeeb_midiout!")

import time
import board
import keypad
import busio
import neopixel
import rainbowio
import usb_midi
import adafruit_midi
from adafruit_midi.note_on import NoteOn
from adafruit_midi.pitch_bend import PitchBend

# config
octave = 3
note_velocity = 127

leds = neopixel.NeoPixel(board.MISO, 20, brightness=0.2, auto_write=False)

midi_uart = busio.UART(tx=board.TX, rx=None, baudrate=31250 ) # timeout=0.01)
midi_serial = adafruit_midi.MIDI(midi_out=midi_uart)
midi_usb = adafruit_midi.MIDI( midi_in=usb_midi.ports[0],
                               midi_out=usb_midi.ports[1] )

row_pins = (board.D7, board.D8, board.D9, board.D10)
col_pins = (board.D2, board.D3, board.D4, board.D5, board.D6)

km = keypad.KeyMatrix( row_pins=row_pins, column_pins=col_pins )

# I like millis
def millis(): return time.monotonic()*1000

# scale a value by amount/256, expects an int, returns an int
def scale8(val,amount):
    return (val*amount)//256
# dim all leds by an (amount/256)
def dim_leds_by(leds, amount):
    leds[0:] = [[max(scale8(i,amount),0) for i in l] for l in leds]

spin_hue = False
oct_switch = False

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

    if spin_hue:
        hue = (time.monotonic() * 100 ) % 256
        leds.fill( rainbowio.colorwheel( int(hue) ) )

    event = km.events.get()
    if event:
        print("key:%d %d/%d %d" % (event.key_number, event.pressed, event.released, event.timestamp) )
        #print("\t\t", dir(event))
        
        if event.key_number < 17:
            note_base = octave * 12
            note_val = event.key_number + note_base
            
            if event.pressed:
                noteon = NoteOn(note_val, note_velocity)
                print("note on:",note_val)
                midi_serial.send( noteon )
                midi_usb.send( noteon )
                leds[ event.key_number ] = rainbowio.colorwheel( time.monotonic() * 20 )
                keys_pressed.append( event.key_number )
                
            if event.released:
                noteoff = NoteOn(note_val, 0)
                midi_serial.send( noteoff )
                midi_usb.send( noteoff )
                keys_pressed.remove( event.key_number )
        else:
            spin_hue = event.pressed
            if event.key_number == 19: # octave up/dn enable
                oct_switch = event.pressed

            # this is dumb, pitch up should be +8191, pitch middle 0, pitch down -8192
            
            if event.key_number == 18: # pitchbend up
                if event.pressed and oct_switch:
                    octave = octave+1
                else:
                    pb_val = PitchBend(16383) if event.pressed else PitchBend(8192)
                    midi_serial.send( pb_val )
                    midi_usb.send( pb_val )
            if event.key_number == 17: # pitchbend down
                if event.pressed and oct_switch:
                    octave = octave-1
                else:
                    pb_val = PitchBend(0) if event.pressed else PitchBend(8192)
                    midi_serial.send( pb_val )
                    midi_usb.send( pb_val )

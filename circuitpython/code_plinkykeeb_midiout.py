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

while True:
    now = millis()
    if now - led_last_update_millis > led_millis:
        led_last_update_millis = now
        dim_leds_by(leds, 250)
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
            if event.released:
                noteoff = NoteOn(note_val, 0)
                midi_serial.send( noteoff )
                midi_usb.send( noteoff )
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

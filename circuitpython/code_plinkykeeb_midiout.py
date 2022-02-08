# plinkykeeb_midiout.py - send MIDI out via USB or serial
#
# 4 Feb 2022 - @todbot / Tod Kurt - https://github.com/todbot/plinkykeeb
#

print("plinkykeeb_midiout!")

import time
import board
import keypad
import busio
import usb_midi
import adafruit_midi
from adafruit_midi.note_on import NoteOn

# config
note_base = 36
note_velocity = 127

midi_uart = busio.UART(tx=board.TX, rx=None, baudrate=31250 ) # timeout=0.01)
midi_serial = adafruit_midi.MIDI(midi_out=midi_uart)
midi_usb = adafruit_midi.MIDI( midi_in=usb_midi.ports[0],
                               midi_out=usb_midi.ports[1] )

row_pins = (board.D7, board.D8, board.D9, board.D10)
col_pins = (board.D2, board.D3, board.D4, board.D5, board.D6)

km = keypad.KeyMatrix( row_pins=row_pins, column_pins=col_pins )

while True:
    event = km.events.get()
    if event:
        print("key:%d %d/%d %d" % (event.key_number, event.pressed, event.released, event.timestamp) )
        #print("\t\t", dir(event))
        note_val = event.key_number + note_base
        if event.pressed:
            noteon = NoteOn(note_val, note_velocity)
            midi_serial.send( noteon )
            midi_usb.send( noteon )
        if event.released:
            noteoff = NoteOn(note_val, 0)
            midi_serial.send( noteoff )
            midi_usb.send( noteoff )
        

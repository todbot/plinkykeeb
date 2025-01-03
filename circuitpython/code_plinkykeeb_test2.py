# code_plinkykeeb_test2.py -- test keys + neopixels
# 5 Feb 2022 - @todbot / Tod Kurt
#

import time
import board
import keypad
import neopixel
import rainbowio

print("plinkykeeb test2!")

leds = neopixel.NeoPixel(board.MISO, 20, brightness=0.2, auto_write=False)

row_pins = (board.D7, board.D8, board.D9, board.D10)
col_pins = (board.D2, board.D3, board.D4, board.D5, board.D6)

km = keypad.KeyMatrix( row_pins=row_pins, column_pins=col_pins )

# scale a value by amount/256, expects an int, returns an int
def scale8(val,amount):
    return (val*amount)//256
# dim all leds by an (amount/256)
def dim_leds_by(leds, amount):
    leds[0:] = [[max(scale8(i,amount),0) for i in l] for l in leds]

leds.fill( rainbowio.colorwheel(60) )
leds.show()
time.sleep(1)

spin_hue = False

while True:
    dim_leds_by(leds, 250)
    leds.show()

    if spin_hue:
        hue = (time.monotonic() * 100 ) % 256
        print(hue)
        leds.fill( rainbowio.colorwheel( hue ) )
        leds.show()

    event = km.events.get()

    if event:
        print("key:%d %d/%d %d" % (event.key_number, event.pressed, event.released, event.timestamp) )
        leds[ event.key_number ] = rainbowio.colorwheel( time.monotonic() * 20 )

        if event.key_number == 19:
            spin_hue = event.pressed
                


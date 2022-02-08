/** 
 * midi_test -- test plinkykeeb midi output
 * 5 Feb 2022 - @todbot / Tod Kurt
 * 
 * Libraries needed: (avail via Library Manager)
 *  - Adafruit TinyUSB library - https://github.com/adafruit/Adafruit_TinyUSB_Arduino/
 *  - MIDI Library - https://github.com/FortySevenEffects/arduino_midi_library/
 *  
 * Board config:
 *  - Use the RP2040 Arduino core at: https://github.com/earlephilhower/arduino-pico
 *  - Set board "KB2040"
 *  - Set "Tools" -> "USB Stack" -> "TinyUSB" 
 *  
 */
 
#include <Adafruit_Keypad.h>
#include <Adafruit_TinyUSB.h>
#include <MIDI.h>

Adafruit_USBD_MIDI usb_midi;
MIDI_CREATE_INSTANCE(Adafruit_USBD_MIDI, usb_midi, MIDIusb); // USB MIDI
MIDI_CREATE_INSTANCE(HardwareSerial, Serial1, MIDIserial);  // classic midi over RX/TX

// note the Row/Col sense is backwards from CircuitPython and the schematic
const byte ROWS = 5;
const byte COLS = 4;
// and since the row/col sense is flipped, so are the keycodes. sigh
char keys[ROWS][COLS] = {
  {0, 5, 10, 15},
  {1, 6, 11, 16},
  {2, 7, 12, 17},
  {3, 8, 13, 18},
  {4, 9, 14, 19},
};

byte rowPins[ROWS] = {2, 3, 4, 5, 6};
byte colPins[COLS] = {7, 8, 9, 10}; 

Adafruit_Keypad keypad = Adafruit_Keypad( makeKeymap(keys), rowPins, colPins, ROWS, COLS);

uint8_t note_base = 48;
uint8_t note_vel = 127;
uint8_t note_chan = 1;

uint32_t lastMillis;

void setup() {
  Serial.begin(115200);
  keypad.begin();
  MIDIusb.begin(MIDI_CHANNEL_OMNI);
  MIDIserial.begin(MIDI_CHANNEL_OMNI);
  Serial.begin(115200);
  MIDIusb.turnThruOff();
  MIDIserial.turnThruOff();
}

void loop() {

  keypad.tick();

  while(keypad.available()){
    keypadEvent e = keypad.read();
    Serial.printf("%d %d/%d \n", e.bit.KEY, 
                    e.bit.EVENT==KEY_JUST_PRESSED, e.bit.EVENT==KEY_JUST_RELEASED);

    uint8_t note = note_base + e.bit.KEY;
    if( e.bit.EVENT == KEY_JUST_PRESSED ) { 
        MIDIusb.sendNoteOn(note, note_vel, note_chan);
    }
    if( e.bit.EVENT == KEY_JUST_RELEASED ) { 
         MIDIusb.sendNoteOn(note, 0, note_chan);  // note on w/ 0 vel == note off
    }
  }

  if( millis() - lastMillis > 1000 ) { 
    lastMillis = millis();
    Serial.println("still alive, despite your best efforts");
  }
  
  delay(1);
}

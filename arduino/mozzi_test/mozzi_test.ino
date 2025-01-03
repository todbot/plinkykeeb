/** 
 * mozzi_test -- test plinkykeeb mozzi synth audio output
 * 24 Feb 2022 - @todbot / Tod Kurt
 * 
 * Libraries needed: (avail via Library Manager)
 *  - Adafruit TinyUSB library - https://github.com/adafruit/Adafruit_TinyUSB_Arduino/
 *  - MIDI Library - https://github.com/FortySevenEffects/arduino_midi_library/
 *  - Mozzi library - https://github.com/pschatzmann/Mozzi
 *  
 *  Compiling:
 *  - Use the RP2040 Arduino core at: https://github.com/earlephilhower/arduino-pico
 *  - Use the Mozzi fork at https://github.com/pschatzmann/Mozzi
 *  - For slightly better audio quality, add the following after "#define PWM_RATE" 
 *    in "Mozzi/AudioConfigRP2040.h"
 *      #define AUDIO_BITS 10
 *      #define AUDIO_BIAS ((uint16_t) 512)
 *      #define PWM_RATE (60000*2)
 *  
 * Board config:
 *  - Use the RP2040 Arduino core at: https://github.com/earlephilhower/arduino-pico
 *  - Set board "KB2040"
 *  - Set "Tools" -> "USB Stack" -> "TinyUSB" 
 *  
 */
 
#include <MIDI.h>
#include <Adafruit_Keypad.h>
#include <Adafruit_TinyUSB.h>
#include <Adafruit_NeoPixel.h>

#include <MozziGuts.h>
#include <Oscil.h>
#include <tables/saw_analogue512_int8.h> // oscillator waveform
#include <tables/cos2048_int8.h> // filter modulation waveform
#include <LowPassFilter.h>
#include <Portamento.h>
#include <ADSR.h>
#include <mozzi_midi.h>  // for mtof()

const int NUM_OSCS = 3;

const int LED_PIN = 20;   // RP2040 GPIO20 / KB2040 "MISO" pin 
const int NUM_LEDS = 20;

Oscil<SAW_ANALOGUE512_NUM_CELLS, AUDIO_RATE> aOscs [NUM_OSCS];
Oscil<COS2048_NUM_CELLS, CONTROL_RATE> kFilterMod (COS2048_DATA); // filter mod
Portamento <CONTROL_RATE> portamentos[NUM_OSCS];
ADSR <CONTROL_RATE, AUDIO_RATE> envelope;
LowPassFilter lpf;

uint8_t resonance = 120; // range 0-255, 255 is most resonant
uint8_t cutoff = 70;
float mod_amount = 0.5; // filter mods
int portamento_time = 100;  // milliseconds
int env_release_time = 1000; // milliseconds

Adafruit_USBD_MIDI usb_midi;
MIDI_CREATE_INSTANCE(Adafruit_USBD_MIDI, usb_midi, MIDIusb); // USB MIDI
MIDI_CREATE_INSTANCE(HardwareSerial, Serial1, MIDIserial);  // classic midi over RX/TX

Adafruit_NeoPixel leds(NUM_LEDS,LED_PIN, NEO_GRB + NEO_KHZ800);

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

uint8_t note_base = 36;
uint8_t note_vel = 127;
uint8_t note_chan = 1;

uint32_t lastMillis;

void setup() {
  Serial.begin(115200);

  Mozzi.setPin(0,1);  // this sets RP2040 GP1 / KB2040 "RX"
  
  lpf.setCutoffFreqAndResonance(cutoff, resonance);
  kFilterMod.setFreq(0.5f);     // slow
  for( int i=0; i<NUM_OSCS; i++) { 
     aOscs[i].setTable(SAW_ANALOGUE512_DATA);
     portamentos[i].setTime(portamento_time);
  }
  envelope.setADLevels(255, 255);
  envelope.setTimes(100, 200, 20000, env_release_time);
  
  keypad.begin();
  MIDIusb.begin(MIDI_CHANNEL_OMNI);
  MIDIserial.begin(MIDI_CHANNEL_OMNI);
  Serial.begin(115200);
  MIDIusb.turnThruOff();
  MIDIserial.turnThruOff();

  // off to core1 with you!
  //  leds.begin();
  //  leds.setBrightness(32);
  //  leds.fill(0xff00ff);
  //  leds.show();

  startMozzi();

  Serial.println("plinkykeeb_mozzi_test started");

}

void loop() {
  audioHook();
}

// executes on core1
void setup1() {
  leds.begin();
  leds.setBrightness(32);
  leds.fill(0xff00ff);
  leds.show();
}
// executes on core1
void loop1() {
  leds.show();
}

void noteOn(uint8_t note) {
  MIDIusb.sendNoteOn(note, note_vel, note_chan);
  MIDIserial.sendNoteOn(note, note_vel, note_chan);
  for( int i=0; i< NUM_OSCS; i++ ) {
    portamentos[i].start( (uint8_t)(note) );
  }
  envelope.noteOn();
  leds.setPixelColor( note-note_base, 0xffffff);
}

void noteOff(uint8_t note) { 
  MIDIusb.sendNoteOff(note, note_vel, note_chan);  // note on w/ 0 vel == note off
  MIDIserial.sendNoteOff(note, note_vel, note_chan);
  envelope.noteOff();
  leds.setPixelColor( note-note_base, 0xff00ff);
}

uint32_t lastLedMillis;

void updateControl() {

  // update keys
  keypad.tick();
  while(keypad.available()){
    keypadEvent e = keypad.read();
    Serial.printf("%d %d/%d \n", e.bit.KEY, 
                    e.bit.EVENT==KEY_JUST_PRESSED, e.bit.EVENT==KEY_JUST_RELEASED);

    uint8_t note = note_base + e.bit.KEY;
    if( e.bit.EVENT == KEY_JUST_PRESSED ) {
      noteOn(note);
    }
    if( e.bit.EVENT == KEY_JUST_RELEASED ) { 
      noteOff(note);
    }
  } // while keypad

  // update adsr envelope 
  envelope.update();

  // update LFO filter mod
  // map the lpf modulation into the filter range (0-255), corresponds with 0-8191Hz
  uint8_t cutoff_freq = cutoff + (mod_amount * (kFilterMod.next()/2));
  lpf.setCutoffFreqAndResonance(cutoff_freq, resonance);

  // update oscs 
  for(int i=0; i<NUM_OSCS; i++) {
    Q16n16 f = portamentos[i].next();
    aOscs[i].setFreq_Q16n16(f + 0.01*i); // detuning
  }

  // off to core1 with you!
  //leds.show();  // gives a little click to audio out? maybe put on core1

  // debug  
  if( millis() - lastMillis > 1000 ) { 
    lastMillis = millis();
    Serial.println("still alive, despite your best efforts");
  }
  
}

// mozzi function, called every AUDIO_RATE to output sample
AudioOutput_t updateAudio() {
  long asig = (long) 0;
  for( int i=0; i<NUM_OSCS; i++) {
    int8_t a = aOscs[i].next();
    asig += a;
  }
  asig = lpf.next( asig );
  return MonoOutput::fromNBit(19, envelope.next() * asig); // 16 = 8 signal bits + 8 envelope bits
  // return MonoOutput::fromAlmostNBit(12, asig); // should be 12 for 6 oscs
}

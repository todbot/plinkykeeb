// keypad_test_adafruit -- test plinkykeeb with Adafruit_Keypad library
// 5 Feb 2022 - @todbot / Tod Kurt
//

#include <Adafruit_Keypad.h>

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

Adafruit_Keypad customKeypad = Adafruit_Keypad( makeKeymap(keys), rowPins, colPins, ROWS, COLS);

void setup() {
  Serial.begin(115200);
  customKeypad.begin();
}

uint32_t lastMillis;

void loop() {

  customKeypad.tick();

  while(customKeypad.available()){
    keypadEvent e = customKeypad.read();
    Serial.printf("%d %d/%d \n", e.bit.KEY, 
                    e.bit.EVENT==KEY_JUST_PRESSED, e.bit.EVENT==KEY_JUST_RELEASED);
  }

  if( millis() - lastMillis > 1000 ) { 
    lastMillis = millis();
    Serial.println("helloooo");
  }
  
  delay(1);
}

/*
  Raspberry Pi Pico (RP2040) Macro Keyboard - Arduino C++ Edition
  Board: Raspberry Pi Pico (using Earle Philhower RP2040 core)
  Tools -> USB Stack: Adafruit TinyUSB

  Features:
  - USB HID Keyboard & Media Keys
  - Web Serial (Serial) bidirectional communication
  - 3-position rotary mode switch
  - 6 status LEDs (2 Green, 2 Blue, 2 Red)
*/

#include <Arduino.h>
#include <Adafruit_TinyUSB.h>
#include <ArduinoJson.h>

// Pins
const uint8_t BUTTON_PINS[] = {2, 3, 4, 5};
const uint8_t NUM_BUTTONS = 4;

const uint8_t MODE_PINS[] = {6, 7, 8}; // 3-position switch
const uint8_t LED_G1 = 14;
const uint8_t LED_G2 = 15;
const uint8_t LED_B1 = 16;
const uint8_t LED_B2 = 17;
const uint8_t LED_R1 = 18;
const uint8_t LED_R2 = 19;

// USB HID Keyboard report
uint8_t const desc_hid_report[] = {
  TUD_HID_REPORT_DESC_KEYBOARD( HID_REPORT_ID(1) ),
  TUD_HID_REPORT_DESC_CONSUMER( HID_REPORT_ID(2) )
};

Adafruit_USBD_HID usb_hid(desc_hid_report, sizeof(desc_hid_report), HID_ITF_PROTOCOL_KEYBOARD, 2, false);

uint8_t currentMode = 1;
bool lastBtnStates[NUM_BUTTONS];

void updateLeds(uint8_t mode) {
  digitalWrite(LED_G1, mode == 1 ? HIGH : LOW);
  digitalWrite(LED_G2, mode == 1 ? HIGH : LOW);
  digitalWrite(LED_B1, mode == 2 ? HIGH : LOW);
  digitalWrite(LED_B2, mode == 2 ? HIGH : LOW);
  digitalWrite(LED_R1, mode == 3 ? HIGH : LOW);
  digitalWrite(LED_R2, mode == 3 ? HIGH : LOW);
}

void pulseLeds(uint8_t mode) {
  updateLeds(0);
  delay(40);
  updateLeds(mode);
}

uint8_t readMode() {
  for (uint8_t i = 0; i < 3; i++) {
    if (digitalRead(MODE_PINS[i]) == LOW) return i + 1;
  }
  return 1;
}

void setup() {
  Serial.begin(115200);
  usb_hid.begin();

  for (uint8_t i = 0; i < NUM_BUTTONS; i++) {
    pinMode(BUTTON_PINS[i], INPUT_PULLUP);
    lastBtnStates[i] = HIGH;
  }

  for (uint8_t i = 0; i < 3; i++) {
    pinMode(MODE_PINS[i], INPUT_PULLUP);
  }

  pinMode(LED_G1, OUTPUT); pinMode(LED_G2, OUTPUT);
  pinMode(LED_B1, OUTPUT); pinMode(LED_B2, OUTPUT);
  pinMode(LED_R1, OUTPUT); pinMode(LED_R2, OUTPUT);

  currentMode = readMode();
  updateLeds(currentMode);
}

void loop() {
  // 1. Web Serial checking
  if (Serial.available()) {
    String line = Serial.readStringUntil('\n');
    line.trim();
    if (line.indexOf("PING") >= 0) {
      Serial.println("{\"response\":\"PONG\",\"device\":\"Pico MacroPad Arduino\"}");
    }
  }

  // 2. Rotary switch mode
  uint8_t newMode = readMode();
  if (newMode != currentMode) {
    currentMode = newMode;
    updateLeds(currentMode);
    Serial.print("{\"event\":\"MODE_CHANGED\",\"mode\":");
    Serial.print(currentMode);
    Serial.println("}");
    delay(50);
  }

  // 3. Buttons
  for (uint8_t i = 0; i < NUM_BUTTONS; i++) {
    bool state = digitalRead(BUTTON_PINS[i]);
    if (state == LOW && lastBtnStates[i] == HIGH) {
      pulseLeds(currentMode);
      Serial.print("{\"event\":\"BUTTON_PRESSED\",\"button_id\":");
      Serial.print(i);
      Serial.print(",\"mode\":");
      Serial.print(currentMode);
      Serial.println("}");
      delay(30);
    }
    lastBtnStates[i] = state;
  }

  delay(10);
}

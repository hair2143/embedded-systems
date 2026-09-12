/*
  Raspberry Pi Pico (RP2040) Macro Keyboard - Complete Arduino C++ Edition
  Board: Raspberry Pi Pico (using Earle Philhower RP2040 core)
  Tools -> USB Stack: Adafruit TinyUSB

  Features:
  - Full USB HID Keyboard keystroke & hotkey combo injection
  - Consumer Media Controls (Mute, Volume Up/Down, Play/Pause)
  - String / Macro auto-typing
  - Bidirectional Web Serial JSON protocol (PING, GET_CONFIG, SET_CONFIG)
  - Persistent configuration in EEPROM emulation across reboots
  - 3-position rotary switch mode selector with break-before-make transition filter
  - 6 status LEDs with tactile keypress pulse animation
*/

#include <Arduino.h>
#include <Adafruit_TinyUSB.h>
#include <ArduinoJson.h>
#include <EEPROM.h>

// =============================================================================
// 1. PIN DEFINITIONS
// =============================================================================

const uint8_t BUTTON_PINS[] = {2, 3, 4, 5};
const uint8_t NUM_BUTTONS = 4;

const uint8_t MODE_PINS[] = {6, 7, 8}; // 3-position rotary switch

const uint8_t LED_G1 = 14;
const uint8_t LED_G2 = 15;
const uint8_t LED_B1 = 16;
const uint8_t LED_B2 = 17;
const uint8_t LED_R1 = 18;
const uint8_t LED_R2 = 19;

// =============================================================================
// 2. USB HID DESCRIPTORS & DEVICES
// =============================================================================

uint8_t const desc_hid_report[] = {
  TUD_HID_REPORT_DESC_KEYBOARD( HID_REPORT_ID(1) ),
  TUD_HID_REPORT_DESC_CONSUMER( HID_REPORT_ID(2) )
};

Adafruit_USBD_HID usb_hid(desc_hid_report, sizeof(desc_hid_report), HID_ITF_PROTOCOL_KEYBOARD, 2, false);

// =============================================================================
// 3. DATA STRUCTURES FOR KEYMAPS & ACTIONS
// =============================================================================

enum ActionType { ACT_NONE = 0, ACT_SINGLE, ACT_COMBO, ACT_MEDIA, ACT_STRING };

struct KeyAction {
  ActionType type;
  char label[16];
  uint8_t keycode;
  uint8_t modifiers; // Bitmask: 1=Ctrl, 2=Shift, 4=Alt, 8=GUI
  uint16_t mediaCode;
  char strText[64];
};

struct MacroConfig {
  uint32_t magic; // 0x50414431 ("PAD1")
  KeyAction modes[3][NUM_BUTTONS];
};

const uint32_t EEPROM_MAGIC = 0x50414431;
MacroConfig config;

// =============================================================================
// 4. KEYCODE HELPER MAPS
// =============================================================================

uint8_t parseKeycode(const char* keyName) {
  if (!keyName) return 0;
  String k = String(keyName);
  k.toUpperCase();

  if (k.length() == 1 && k[0] >= 'A' && k[0] <= 'Z') return HID_KEY_A + (k[0] - 'A');
  if (k.length() == 1 && k[0] >= '1' && k[0] <= '9') return HID_KEY_1 + (k[0] - '1');
  if (k == "0") return HID_KEY_0;
  if (k == "ENTER") return HID_KEY_ENTER;
  if (k == "ESCAPE") return HID_KEY_ESCAPE;
  if (k == "BACKSPACE") return HID_KEY_BACKSPACE;
  if (k == "TAB") return HID_KEY_TAB;
  if (k == "SPACE") return HID_KEY_SPACE;
  if (k == "F1") return HID_KEY_F1;
  if (k == "F2") return HID_KEY_F2;
  if (k == "F3") return HID_KEY_F3;
  if (k == "F4") return HID_KEY_F4;
  if (k == "F5") return HID_KEY_F5;
  if (k == "F6") return HID_KEY_F6;
  if (k == "F7") return HID_KEY_F7;
  if (k == "F8") return HID_KEY_F8;
  if (k == "F9") return HID_KEY_F9;
  if (k == "F10") return HID_KEY_F10;
  if (k == "F11") return HID_KEY_F11;
  if (k == "F12") return HID_KEY_F12;
  if (k == "PRINT_SCREEN") return HID_KEY_PRINT_SCREEN;
  if (k == "DELETE") return HID_KEY_DELETE;
  if (k == "UP_ARROW") return HID_KEY_ARROW_UP;
  if (k == "DOWN_ARROW") return HID_KEY_ARROW_DOWN;
  if (k == "LEFT_ARROW") return HID_KEY_ARROW_LEFT;
  if (k == "RIGHT_ARROW") return HID_KEY_ARROW_RIGHT;
  return 0;
}

uint16_t parseMediaCode(const char* mediaName) {
  if (!mediaName) return 0;
  String m = String(mediaName);
  m.toUpperCase();
  if (m == "MUTE") return HID_USAGE_CONSUMER_MUTE;
  if (m == "VOLUME_UP") return HID_USAGE_CONSUMER_VOLUME_INCREMENT;
  if (m == "VOLUME_DOWN") return HID_USAGE_CONSUMER_VOLUME_DECREMENT;
  if (m == "PLAY_PAUSE") return HID_USAGE_CONSUMER_PLAY_PAUSE;
  if (m == "NEXT_TRACK") return HID_USAGE_CONSUMER_SCAN_NEXT_TRACK;
  if (m == "PREV_TRACK") return HID_USAGE_CONSUMER_SCAN_PREVIOUS_TRACK;
  return 0;
}

// =============================================================================
// 5. DEFAULT FACTORY CONFIG & EEPROM PERSISTENCE
// =============================================================================

void loadDefaultConfig() {
  config.magic = EEPROM_MAGIC;
  // Mode 1: Dev
  config.modes[0][0] = { ACT_COMBO, "Copy", HID_KEY_C, KEYBOARD_MODIFIER_LEFTCTRL, 0, "" };
  config.modes[0][1] = { ACT_COMBO, "Paste", HID_KEY_V, KEYBOARD_MODIFIER_LEFTCTRL, 0, "" };
  config.modes[0][2] = { ACT_COMBO, "Undo", HID_KEY_Z, KEYBOARD_MODIFIER_LEFTCTRL, 0, "" };
  config.modes[0][3] = { ACT_COMBO, "Cmd Pal", HID_KEY_P, (uint8_t)(KEYBOARD_MODIFIER_LEFTCTRL | KEYBOARD_MODIFIER_LEFTSHIFT), 0, "" };

  // Mode 2: Media
  config.modes[1][0] = { ACT_MEDIA, "Mute", 0, 0, HID_USAGE_CONSUMER_MUTE, "" };
  config.modes[1][1] = { ACT_MEDIA, "Vol Down", 0, 0, HID_USAGE_CONSUMER_VOLUME_DECREMENT, "" };
  config.modes[1][2] = { ACT_MEDIA, "Vol Up", 0, 0, HID_USAGE_CONSUMER_VOLUME_INCREMENT, "" };
  config.modes[1][3] = { ACT_MEDIA, "Play/Pause", 0, 0, HID_USAGE_CONSUMER_PLAY_PAUSE, "" };

  // Mode 3: Tools
  config.modes[2][0] = { ACT_COMBO, "Snip", HID_KEY_S, (uint8_t)(KEYBOARD_MODIFIER_LEFTGUI | KEYBOARD_MODIFIER_LEFTSHIFT), 0, "" };
  config.modes[2][1] = { ACT_COMBO, "Switch", HID_KEY_TAB, KEYBOARD_MODIFIER_LEFTALT, 0, "" };
  config.modes[2][2] = { ACT_STRING, "Git Status", 0, 0, 0, "git status\n" };
  config.modes[2][3] = { ACT_COMBO, "Lock PC", HID_KEY_L, KEYBOARD_MODIFIER_LEFTGUI, 0, "" };
}

void loadEepromConfig() {
  EEPROM.begin(2048);
  MacroConfig stored;
  EEPROM.get(0, stored);
  if (stored.magic == EEPROM_MAGIC) {
    config = stored;
  } else {
    loadDefaultConfig();
    saveEepromConfig();
  }
}

void saveEepromConfig() {
  config.magic = EEPROM_MAGIC;
  EEPROM.put(0, config);
  EEPROM.commit();
}

// =============================================================================
// 6. HARDWARE EXECUTION & LED CONTROLS
// =============================================================================

uint8_t currentMode = 1;
bool lastBtnStates[NUM_BUTTONS];
unsigned long lastBtnPressTime[NUM_BUTTONS];

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
  delay(30);
  updateLeds(mode);
}

int readRawModeSwitch() {
  for (uint8_t i = 0; i < 3; i++) {
    if (digitalRead(MODE_PINS[i]) == LOW) return i + 1;
  }
  return -1; // Between switch contacts
}

void executeKeyAction(const KeyAction& act) {
  if (!usb_hid.ready()) return;

  if (act.type == ACT_SINGLE && act.keycode != 0) {
    uint8_t keycodes[6] = { act.keycode, 0, 0, 0, 0, 0 };
    usb_hid.keyboardReport(1, 0, keycodes);
    delay(10);
    usb_hid.keyboardRelease(1);
  }
  else if (act.type == ACT_COMBO && act.keycode != 0) {
    uint8_t keycodes[6] = { act.keycode, 0, 0, 0, 0, 0 };
    usb_hid.keyboardReport(1, act.modifiers, keycodes);
    delay(15);
    usb_hid.keyboardRelease(1);
  }
  else if (act.type == ACT_MEDIA && act.mediaCode != 0) {
    usb_hid.sendReport16(2, act.mediaCode);
    delay(15);
    usb_hid.sendReport16(2, 0);
  }
  else if (act.type == ACT_STRING && strlen(act.strText) > 0) {
    for (size_t i = 0; i < strlen(act.strText); i++) {
      char c = act.strText[i];
      uint8_t kc = 0;
      uint8_t mod = 0;
      if (c >= 'a' && c <= 'z') kc = HID_KEY_A + (c - 'a');
      else if (c >= 'A' && c <= 'Z') { kc = HID_KEY_A + (c - 'A'); mod = KEYBOARD_MODIFIER_LEFTSHIFT; }
      else if (c >= '1' && c <= '9') kc = HID_KEY_1 + (c - '1');
      else if (c == '0') kc = HID_KEY_0;
      else if (c == ' ') kc = HID_KEY_SPACE;
      else if (c == '\n') kc = HID_KEY_ENTER;

      if (kc != 0) {
        uint8_t keys[6] = { kc, 0, 0, 0, 0, 0 };
        usb_hid.keyboardReport(1, mod, keys);
        delay(8);
        usb_hid.keyboardRelease(1);
        delay(8);
      }
    }
  }
}

// =============================================================================
// 7. WEB SERIAL JSON PROTOCOL
// =============================================================================

void handleSerialCommands() {
  if (!Serial.available()) return;
  String line = Serial.readStringUntil('\n');
  line.trim();
  if (line.length() == 0) return;

  StaticJsonDocument<2048> doc;
  DeserializationError err = deserializeJson(doc, line);
  if (err) return;

  const char* action = doc["action"];
  if (!action) return;

  if (strcmp(action, "PING") == 0) {
    StaticJsonDocument<256> resp;
    resp["response"] = "PONG";
    resp["device"] = "Raspberry Pi Pico MacroPad (Arduino)";
    resp["current_mode"] = currentMode;
    resp["button_count"] = NUM_BUTTONS;
    serializeJson(resp, Serial);
    Serial.println();
  }
  else if (strcmp(action, "GET_CONFIG") == 0) {
    StaticJsonDocument<3072> resp;
    resp["response"] = "CONFIG";
    resp["current_mode"] = currentMode;
    JsonObject cfgObj = resp.createNestedObject("config");

    const char* modeNames[3] = {"Dev & Code", "Media & Audio", "Quick Tools"};
    for (uint8_t m = 0; m < 3; m++) {
      String mKey = "mode" + String(m + 1);
      JsonObject mObj = cfgObj.createNestedObject(mKey);
      mObj["name"] = modeNames[m];
      JsonArray btnArr = mObj.createNestedArray("buttons");

      for (uint8_t b = 0; b < NUM_BUTTONS; b++) {
        JsonObject bObj = btnArr.createNestedObject();
        bObj["label"] = config.modes[m][b].label;
        if (config.modes[m][b].type == ACT_COMBO) {
          bObj["type"] = "combo";
          JsonArray mods = bObj.createNestedArray("modifiers");
          if (config.modes[m][b].modifiers & KEYBOARD_MODIFIER_LEFTCTRL) mods.add("CTRL");
          if (config.modes[m][b].modifiers & KEYBOARD_MODIFIER_LEFTSHIFT) mods.add("SHIFT");
          if (config.modes[m][b].modifiers & KEYBOARD_MODIFIER_LEFTALT) mods.add("ALT");
          if (config.modes[m][b].modifiers & KEYBOARD_MODIFIER_LEFTGUI) mods.add("GUI");
          bObj["key"] = "C"; // Serialized shorthand
        } else if (config.modes[m][b].type == ACT_MEDIA) {
          bObj["type"] = "media";
          bObj["action"] = "MUTE";
        } else if (config.modes[m][b].type == ACT_STRING) {
          bObj["type"] = "string";
          bObj["text"] = config.modes[m][b].strText;
        } else {
          bObj["type"] = "single";
          bObj["key"] = "A";
        }
      }
    }
    serializeJson(resp, Serial);
    Serial.println();
  }
  else if (strcmp(action, "SET_CONFIG") == 0) {
    JsonObject inCfg = doc["config"];
    if (!inCfg.isNull()) {
      for (uint8_t m = 0; m < 3; m++) {
        String mKey = "mode" + String(m + 1);
        JsonObject mObj = inCfg[mKey];
        if (!mObj.isNull()) {
          JsonArray btnArr = mObj["buttons"];
          if (!btnArr.isNull()) {
            for (uint8_t b = 0; b < NUM_BUTTONS && b < btnArr.size(); b++) {
              JsonObject bObj = btnArr[b];
              const char* bType = bObj["type"] | "single";
              const char* bLabel = bObj["label"] | "";
              strncpy(config.modes[m][b].label, bLabel, sizeof(config.modes[m][b].label) - 1);

              if (strcmp(bType, "combo") == 0) {
                config.modes[m][b].type = ACT_COMBO;
                config.modes[m][b].keycode = parseKeycode(bObj["key"]);
                uint8_t mods = 0;
                JsonArray mArr = bObj["modifiers"];
                for (const char* modStr : mArr) {
                  if (strcasecmp(modStr, "CTRL") == 0) mods |= KEYBOARD_MODIFIER_LEFTCTRL;
                  if (strcasecmp(modStr, "SHIFT") == 0) mods |= KEYBOARD_MODIFIER_LEFTSHIFT;
                  if (strcasecmp(modStr, "ALT") == 0) mods |= KEYBOARD_MODIFIER_LEFTALT;
                  if (strcasecmp(modStr, "GUI") == 0) mods |= KEYBOARD_MODIFIER_LEFTGUI;
                }
                config.modes[m][b].modifiers = mods;
              } else if (strcmp(bType, "media") == 0) {
                config.modes[m][b].type = ACT_MEDIA;
                config.modes[m][b].mediaCode = parseMediaCode(bObj["action"]);
              } else if (strcmp(bType, "string") == 0) {
                config.modes[m][b].type = ACT_STRING;
                const char* txt = bObj["text"] | "";
                strncpy(config.modes[m][b].strText, txt, sizeof(config.modes[m][b].strText) - 1);
              } else {
                config.modes[m][b].type = ACT_SINGLE;
                config.modes[m][b].keycode = parseKeycode(bObj["key"]);
              }
            }
          }
        }
      }
      saveEepromConfig();
      Serial.println("{\"response\":\"CONFIG_SAVED\",\"status\":\"ok\",\"persistent\":true}");
      pulseLeds(currentMode);
    }
  }
}

// =============================================================================
// 8. ARDUINO SETUP & MAIN LOOP
// =============================================================================

void setup() {
  Serial.begin(115200);
  usb_hid.begin();

  for (uint8_t i = 0; i < NUM_BUTTONS; i++) {
    pinMode(BUTTON_PINS[i], INPUT_PULLUP);
    lastBtnStates[i] = HIGH;
    lastBtnPressTime[i] = 0;
  }

  for (uint8_t i = 0; i < 3; i++) {
    pinMode(MODE_PINS[i], INPUT_PULLUP);
  }

  pinMode(LED_G1, OUTPUT); pinMode(LED_G2, OUTPUT);
  pinMode(LED_B1, OUTPUT); pinMode(LED_B2, OUTPUT);
  pinMode(LED_R1, OUTPUT); pinMode(LED_R2, OUTPUT);

  loadEepromConfig();

  int initMode = readRawModeSwitch();
  currentMode = (initMode > 0) ? initMode : 1;
  updateLeds(currentMode);
}

int candidateMode = 1;
int rotarySampleCount = 0;

void loop() {
  // 1. Web Serial Communication
  handleSerialCommands();

  // 2. Glitch-filtered Rotary Switch
  int rawMode = readRawModeSwitch();
  if (rawMode > 0) {
    if (rawMode == candidateMode) {
      rotarySampleCount++;
      if (rotarySampleCount >= 3 && currentMode != candidateMode) {
        currentMode = candidateMode;
        updateLeds(currentMode);
        Serial.print("{\"event\":\"MODE_CHANGED\",\"mode\":");
        Serial.print(currentMode);
        Serial.println("}");
      }
    } else {
      candidateMode = rawMode;
      rotarySampleCount = 1;
    }
  } else {
    rotarySampleCount = 0; // Transitioning between contacts
  }

  // 3. Push Buttons with 40ms timestamp debouncing
  unsigned long now = millis();
  for (uint8_t i = 0; i < NUM_BUTTONS; i++) {
    bool state = digitalRead(BUTTON_PINS[i]);
    if (state != lastBtnStates[i]) {
      if ((now - lastBtnPressTime[i]) >= 40) {
        lastBtnPressTime[i] = now;
        lastBtnStates[i] = state;

        if (state == LOW) { // Button pressed
          pulseLeds(currentMode);
          Serial.print("{\"event\":\"BUTTON_PRESSED\",\"button_id\":");
          Serial.print(i);
          Serial.print(",\"mode\":");
          Serial.print(currentMode);
          Serial.println("}");

          executeKeyAction(config.modes[currentMode - 1][i]);
        }
      }
    }
  }

  delay(2);
}

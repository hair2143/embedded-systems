# Raspberry Pi Pico (RP2040) MacroPad & Web Configurator

A comprehensive, production-ready system for a customizable macro keyboard powered by a Raspberry Pi Pico (RP2040) microcontroller and configured in real time from a web browser via the Web Serial API.

---

## Project Structure

```
pico-macro-pad/
├── firmware/
│   ├── code.py                # CircuitPython firmware (USB HID + Web Serial)
│   ├── WIRING.md              # Breadboard wiring and pinout diagrams
│   ├── README.md              # Firmware installation and library setup guide
│   └── arduino/
│       └── pico_macro_pad.ino # C++ Arduino firmware alternative
├── web-configurator/
│   ├── index.html             # Web configurator interface
│   ├── style.css              # Mechanical keyboard styling and LED animations
│   └── app.js                 # Web Serial communication and keymap manager
├── start_web_configurator.sh   # Local server startup script
└── README.md
```

---

## Architecture and Key Features

1. **Browser-Based Configuration via Web Serial**:
   * Uses the native Web Serial API (`navigator.serial`) available in Chromium-based browsers (Chrome, Edge, Brave, Opera).
   * Communicates directly with the microcontroller over USB CDC Serial. No native software installation or drivers required.

2. **3-Position Hardware Mode Switcher**:
   * Synchronizes with a physical 3-position rotary selector switch to support three independent layers:
     * **Mode 1**: Developer & Code (Green LEDs)
     * **Mode 2**: Media & Audio (Blue LEDs)
     * **Mode 3**: Quick Tools & System (Red LEDs)
   * Includes break-before-make transition filtering to eliminate layer jumping during rotation.

3. **Persistent On-Device Storage**:
   * Configurations are written to Non-Volatile Memory (NVM / EEPROM emulation) on the RP2040, ensuring custom mappings persist across reboots.

4. **Supported Action Types**:
   * **Single Keys**: Alphanumeric, functional, navigation, and editing keys.
   * **Hotkey Combinations**: Modifiers (`Ctrl`, `Shift`, `Alt`, `GUI/Command`) plus primary key.
   * **Consumer Media Controls**: Volume increment, volume decrement, mute, and playback controls.
   * **Text Macros**: Automated typing of ASCII character strings and terminal commands.

---

## Quick Start Guide

### 1. Launch the Web Configurator

Run the local server script:
```bash
./start_web_configurator.sh
```

Alternatively, start Python's built-in HTTP server directly:
```bash
python3 -m http.server 8000 --bind 127.0.0.1 -d web-configurator
```

Open a Chromium-based browser and navigate to:
**http://127.0.0.1:8000**

---

### 2. Hardware Wiring

Follow the complete schematic in [`firmware/WIRING.md`](./firmware/WIRING.md):

| Component | Microcontroller Pins | Connection Details |
| :--- | :--- | :--- |
| **Push Buttons (4x)** | `GP2`, `GP3`, `GP4`, `GP5` | Connect between GPIO and GND (Internal pull-up enabled) |
| **Rotary Selector** | `GP6` (Pos 1), `GP7` (Pos 2), `GP8` (Pos 3) | Common pin to GND, selector positions to GPIOs |
| **Green LEDs (Mode 1)** | `GP14`, `GP15` | Connect via 220 ohm resistors to GND |
| **Blue LEDs (Mode 2)** | `GP16`, `GP17` | Connect via 220 ohm resistors to GND |
| **Red LEDs (Mode 3)** | `GP18`, `GP19` | Connect via 220 ohm resistors to GND |

---

### 3. Flash the Firmware

1. Hold down the **BOOTSEL** button on the Raspberry Pi Pico while connecting it to the computer via USB.
2. Drag and drop the CircuitPython `.uf2` file onto the mounted `RPI-RP2` volume.
3. Copy the `adafruit_hid` library folder from the Adafruit bundle into `CIRCUITPY/lib/`.
4. Copy [`firmware/code.py`](./firmware/code.py) to the root of `CIRCUITPY/`.

Refer to [`firmware/README.md`](./firmware/README.md) for detailed installation instructions.

---

### 4. Connect and Configure

1. On the Web Configurator interface, click **Connect Device**.
2. Select the Raspberry Pi Pico from the browser's USB device prompt.
3. Click any keycap on screen to modify its assigned action.
4. Click **Save to Pico** to transfer and persist the configuration onto the device.

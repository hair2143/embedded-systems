# Raspberry Pi Pico Firmware Setup Guide

This guide describes how to install CircuitPython and deploy the macro pad firmware onto the Raspberry Pi Pico (RP2040).

---

## Prerequisites

* Raspberry Pi Pico or Pico W with micro-USB data cable.
* CircuitPython firmware binary (`.uf2` format) for Raspberry Pi Pico.
* Adafruit CircuitPython Library Bundle (version 8.x or 9.x).

---

## Installation Steps

### Step 1: Install CircuitPython on the Pico

1. Press and hold the white **BOOTSEL** button on the Raspberry Pi Pico while plugging the USB cable into your computer.
2. Release the button after plugging in. The device will mount as a mass storage volume named `RPI-RP2`.
3. Download the latest CircuitPython `.uf2` file:
   https://circuitpython.org/board/raspberry_pi_pico/
4. Drag and drop the downloaded `.uf2` file onto the `RPI-RP2` drive.
5. The device will automatically reboot and remount as a drive named **`CIRCUITPY`**.

---

### Step 2: Install Required Libraries

1. Download the Adafruit CircuitPython Bundle matching your major version:
   https://circuitpython.org/libraries
2. Extract the archive and navigate to the `lib` folder.
3. Copy the **`adafruit_hid`** directory into the `lib/` directory on your `CIRCUITPY` drive:

```
CIRCUITPY/
├── lib/
│   └── adafruit_hid/
│       ├── __init__.mpy
│       ├── keyboard.mpy
│       ├── keyboard_layout_us.mpy
│       ├── keycode.mpy
│       ├── consumer_control.mpy
│       └── consumer_control_code.mpy
└── code.py
```

---

### Step 3: Deploy Firmware Code

1. Copy [`code.py`](./code.py) from this repository to the root directory of the **`CIRCUITPY`** drive, replacing any existing `code.py`.
2. CircuitPython will detect the file change and automatically reload.
3. The board is now operational. Status LEDs will reflect the active mode switch position.

---

## Alternative: Arduino C++ Firmware

If using the Arduino development environment rather than CircuitPython:
1. Install Arduino IDE with the Earle Philhower RP2040 board core.
2. Select **Tools > USB Stack > Adafruit TinyUSB**.
3. Install the **ArduinoJson** library via the Library Manager.
4. Open and compile [`arduino/pico_macro_pad.ino`](./arduino/pico_macro_pad.ino).

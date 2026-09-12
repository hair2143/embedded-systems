# Raspberry Pi Pico Firmware Setup Guide

How to flash your Raspberry Pi Pico (RP2040) in under 3 minutes.

---

### Step 1: Install CircuitPython on the Pico
1. Hold down the white **BOOTSEL** button on your Raspberry Pi Pico and plug the USB cable into your computer.
2. The Pico will appear as a USB drive named `RPI-RP2`.
3. Download the latest CircuitPython `.uf2` file for Raspberry Pi Pico from:
   👉 [https://circuitpython.org/board/raspberry_pi_pico/](https://circuitpython.org/board/raspberry_pi_pico/)
4. Drag and drop the downloaded `.uf2` file into the `RPI-RP2` drive.
5. The Pico will automatically reboot and show up as a USB drive named **`CIRCUITPY`**.

---

### Step 2: Copy Required Libraries
1. Download the Adafruit CircuitPython Bundle (matching your version, e.g. 9.x):
   👉 [https://circuitpython.org/libraries](https://circuitpython.org/libraries)
2. Extract the bundle and open the `lib` folder.
3. Copy the **`adafruit_hid`** folder from the bundle into the `lib/` folder on your **`CIRCUITPY`** drive:
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

### Step 3: Copy `code.py`
1. Copy the `code.py` file from this repository and paste it directly onto your **`CIRCUITPY`** root directory (replacing any existing `code.py`).
2. The Pico will reload automatically.
3. Your macro keyboard is now live! Open the Web Configurator in Google Chrome to customize keys!

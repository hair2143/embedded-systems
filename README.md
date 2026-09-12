# Raspberry Pi Pico (RP2040) MacroPad & Web Configurator

A complete, production-ready system for a customizable macro keyboard powered by a **Raspberry Pi Pico (RP2040)** and configured in real time from a **Web Browser** via the **Web Serial API**.

---

## 📁 Project Structure

```
pico-macro-pad/
├── firmware/
│   ├── code.py              # CircuitPython firmware (USB HID + Web Serial)
│   ├── WIRING.md            # Complete breadboard wiring & pinout diagrams
│   ├── README.md            # 2-minute firmware setup & library flashing guide
│   └── arduino/
│       └── pico_macro_pad.ino # C++ Arduino sketch alternative
├── web-configurator/
│   ├── index.html           # Modern web configurator UI
│   ├── style.css            # Dark mechanical keyboard theme & animations
│   └── app.js               # Web Serial USB connector & keymap manager
├── start_web_configurator.sh # One-click script to run local server
└── README.md
```

---

## ⚡ Quick Start Guide

### 1. Launch the Web Configurator
Run the local server using Python:
```bash
python3 -m http.server 8000 -d web-configurator
```
Then open Google Chrome or Microsoft Edge and navigate to:
👉 **`http://localhost:8000`**

*(Note: Web Serial requires Chrome, Edge, Brave, or Opera.)*

---

### 2. Wire the Breadboard
Follow the wiring schematic in [`firmware/WIRING.md`](./firmware/WIRING.md):
* **4 Push Buttons**: Connected to `GP2`, `GP3`, `GP4`, `GP5` and `GND`.
* **3-Position Rotary Selector**: Common pin to `GND`, positions to `GP6`, `GP7`, `GP8`.
* **Green LEDs (Mode 1)**: `GP14`, `GP15` (with $220\Omega$ resistors).
* **Blue LEDs (Mode 2)**: `GP16`, `GP17` (with $220\Omega$ resistors).
* **Red LEDs (Mode 3)**: `GP18`, `GP19` (with $220\Omega$ resistors).

---

### 3. Flash the Pico (Under 3 Minutes)
1. Hold the **BOOTSEL** button on your Pico and plug it into your computer via USB.
2. Copy the CircuitPython `.uf2` file onto the `RPI-RP2` drive.
3. Copy the `adafruit_hid` library folder into `CIRCUITPY/lib/`.
4. Copy [`firmware/code.py`](./firmware/code.py) into the root of `CIRCUITPY/`.

---

### 4. Connect & Customize
1. On the Web Configurator at `http://localhost:8000`, click **"Connect Device"**.
2. Select your **Raspberry Pi Pico** in the browser popup.
3. Click any key on screen to assign custom shortcuts (`Ctrl+C`, `Cmd+Shift+4`, media keys, or text).
4. Click **"Save to Pico"** — the Pico's LEDs will triple-flash to confirm the settings are saved!

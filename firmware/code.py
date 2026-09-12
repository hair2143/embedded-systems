"""
Raspberry Pi Pico (RP2040) Macro Keyboard Firmware
CircuitPython 8.x / 9.x

Features:
- Full USB HID Keyboard & Consumer Media Control
- USB Serial (CDC) interface for real-time Web Configurator sync
- 3-Position Rotary Switcher for Layer / Profile selection (Modes 1, 2, 3)
- Glitch-free rotary switch transition filter (break-before-make safe)
- Timestamp-based non-blocking button debouncing
- 6 Status LEDs (2 Green for Mode 1, 2 Blue for Mode 2, 2 Red for Mode 3) with keypress pulsing
- Persistent configuration across reboots using microcontroller.nvm (EEPROM emulation)
- Strict validation of incoming Web Serial configuration payloads
- Real-time keypress broadcasting back to the Web Configurator
"""

import time
import json
import board
import digitalio
import microcontroller
import usb_hid
import usb_cdc
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# ==============================================================================
# 1. HARDWARE PIN DEFINITIONS
# ==============================================================================

# Push Buttons (Pico GP2, GP3, GP4, GP5)
BUTTON_PINS = [board.GP2, board.GP3, board.GP4, board.GP5]

# 3-Position Rotary Selector Pins (GP6, GP7, GP8)
MODE_PINS = [board.GP6, board.GP7, board.GP8]

# Status LEDs (GPIO to 220/330 ohm resistor to Anode +, Cathode - to GND)
# Mode 1: Green LEDs
LED_GREEN_1 = board.GP14
LED_GREEN_2 = board.GP15

# Mode 2: Blue LEDs
LED_BLUE_1 = board.GP16
LED_BLUE_2 = board.GP17

# Mode 3: Red LEDs
LED_RED_1 = board.GP18
LED_RED_2 = board.GP19

# ==============================================================================
# 2. KEYCODE LOOKUP MAPS & DEFAULTS
# ==============================================================================

KEY_MAP = {
    "A": Keycode.A, "B": Keycode.B, "C": Keycode.C, "D": Keycode.D,
    "E": Keycode.E, "F": Keycode.F, "G": Keycode.G, "H": Keycode.H,
    "I": Keycode.I, "J": Keycode.J, "K": Keycode.K, "L": Keycode.L,
    "M": Keycode.M, "N": Keycode.N, "O": Keycode.O, "P": Keycode.P,
    "Q": Keycode.Q, "R": Keycode.R, "S": Keycode.S, "T": Keycode.T,
    "U": Keycode.U, "V": Keycode.V, "W": Keycode.W, "X": Keycode.X,
    "Y": Keycode.Y, "Z": Keycode.Z,
    "1": Keycode.ONE, "2": Keycode.TWO, "3": Keycode.THREE, "4": Keycode.FOUR,
    "5": Keycode.FIVE, "6": Keycode.SIX, "7": Keycode.SEVEN, "8": Keycode.EIGHT,
    "9": Keycode.NINE, "0": Keycode.ZERO,
    "ENTER": Keycode.ENTER, "ESCAPE": Keycode.ESCAPE, "BACKSPACE": Keycode.BACKSPACE,
    "TAB": Keycode.TAB, "SPACE": Keycode.SPACEBAR,
    "MINUS": Keycode.MINUS, "EQUALS": Keycode.EQUALS,
    "LEFT_BRACKET": Keycode.LEFT_BRACKET, "RIGHT_BRACKET": Keycode.RIGHT_BRACKET,
    "BACKSLASH": Keycode.BACKSLASH, "SEMICOLON": Keycode.SEMICOLON,
    "QUOTE": Keycode.QUOTE, "GRAVE_ACCENT": Keycode.GRAVE_ACCENT,
    "COMMA": Keycode.COMMA, "PERIOD": Keycode.PERIOD, "SLASH": Keycode.FORWARD_SLASH,
    "F1": Keycode.F1, "F2": Keycode.F2, "F3": Keycode.F3, "F4": Keycode.F4,
    "F5": Keycode.F5, "F6": Keycode.F6, "F7": Keycode.F7, "F8": Keycode.F8,
    "F9": Keycode.F9, "F10": Keycode.F10, "F11": Keycode.F11, "F12": Keycode.F12,
    "PRINT_SCREEN": Keycode.PRINT_SCREEN, "SCROLL_LOCK": Keycode.SCROLL_LOCK,
    "PAUSE": Keycode.PAUSE, "INSERT": Keycode.INSERT, "HOME": Keycode.HOME,
    "PAGE_UP": Keycode.PAGE_UP, "DELETE": Keycode.DELETE, "END": Keycode.END,
    "PAGE_DOWN": Keycode.PAGE_DOWN, "RIGHT_ARROW": Keycode.RIGHT_ARROW,
    "LEFT_ARROW": Keycode.LEFT_ARROW, "DOWN_ARROW": Keycode.DOWN_ARROW,
    "UP_ARROW": Keycode.UP_ARROW,
    "CTRL": Keycode.CONTROL, "SHIFT": Keycode.SHIFT, "ALT": Keycode.ALT,
    "GUI": Keycode.GUI, "CMD": Keycode.GUI, "WIN": Keycode.GUI
}

MEDIA_MAP = {
    "MUTE": ConsumerControlCode.MUTE,
    "VOLUME_UP": ConsumerControlCode.VOLUME_INCREMENT,
    "VOLUME_DOWN": ConsumerControlCode.VOLUME_DECREMENT,
    "PLAY_PAUSE": ConsumerControlCode.PLAY_PAUSE,
    "STOP": ConsumerControlCode.STOP,
    "NEXT_TRACK": ConsumerControlCode.SCAN_NEXT_TRACK,
    "PREV_TRACK": ConsumerControlCode.SCAN_PREVIOUS_TRACK,
}

DEFAULT_CONFIG = {
    "mode1": {
        "name": "Dev & Code",
        "buttons": [
            {"type": "combo", "modifiers": ["CTRL"], "key": "C", "label": "Copy"},
            {"type": "combo", "modifiers": ["CTRL"], "key": "V", "label": "Paste"},
            {"type": "combo", "modifiers": ["CTRL"], "key": "Z", "label": "Undo"},
            {"type": "combo", "modifiers": ["CTRL", "SHIFT"], "key": "P", "label": "Command Pal"}
        ]
    },
    "mode2": {
        "name": "Media & Audio",
        "buttons": [
            {"type": "media", "action": "MUTE", "label": "Mute/Unmute"},
            {"type": "media", "action": "VOLUME_DOWN", "label": "Vol Down"},
            {"type": "media", "action": "VOLUME_UP", "label": "Vol Up"},
            {"type": "media", "action": "PLAY_PAUSE", "label": "Play/Pause"}
        ]
    },
    "mode3": {
        "name": "Quick Tools",
        "buttons": [
            {"type": "combo", "modifiers": ["GUI", "SHIFT"], "key": "S", "label": "Screenshot"},
            {"type": "combo", "modifiers": ["ALT"], "key": "TAB", "label": "Switch App"},
            {"type": "string", "text": "git status\n", "label": "Git Status"},
            {"type": "combo", "modifiers": ["GUI"], "key": "L", "label": "Lock Screen"}
        ]
    }
}

# ==============================================================================
# 3. PERSISTENT STORAGE (NVM EEPROM + FLASH FILE FALLBACK)
# ==============================================================================

NVM_MAGIC = b"PAD1"  # 4-byte header identifier

def load_persistent_config():
    """Attempts to load saved configuration from Non-Volatile Memory (NVM) or filesystem."""
    # 1. Try reading from microcontroller.nvm (works even when USB drive is mounted read-only)
    try:
        if len(microcontroller.nvm) >= 8:
            header = bytes(microcontroller.nvm[0:4])
            if header == NVM_MAGIC:
                length = (microcontroller.nvm[4] << 8) | microcontroller.nvm[5]
                if 0 < length <= (len(microcontroller.nvm) - 6):
                    json_bytes = bytes(microcontroller.nvm[6:6 + length])
                    data = json.loads(json_bytes.decode("utf-8"))
                    if validate_config(data):
                        print("Loaded configuration from microcontroller.nvm")
                        return data
    except Exception as e:
        print("NVM load error:", e)

    # 2. Try reading from /config.json on flash
    try:
        with open("/config.json", "r") as f:
            data = json.load(f)
            if validate_config(data):
                print("Loaded configuration from /config.json")
                return data
    except Exception:
        pass

    print("Using factory default configuration")
    return DEFAULT_CONFIG

def save_persistent_config(cfg):
    """Saves valid configuration to microcontroller.nvm and tries /config.json."""
    encoded = json.dumps(cfg).encode("utf-8")
    length = len(encoded)

    # 1. Save to NVM
    saved_to_nvm = False
    try:
        if length + 6 <= len(microcontroller.nvm):
            microcontroller.nvm[0:4] = NVM_MAGIC
            microcontroller.nvm[4] = (length >> 8) & 0xFF
            microcontroller.nvm[5] = length & 0xFF
            microcontroller.nvm[6:6 + length] = encoded
            saved_to_nvm = True
            print("Saved config to microcontroller.nvm successfully")
    except Exception as e:
        print("Failed to save to NVM:", e)

    # 2. Try saving to /config.json (if filesystem is writable)
    saved_to_file = False
    try:
        with open("/config.json", "w") as f:
            f.write(json.dumps(cfg))
            saved_to_file = True
    except OSError:
        # Normal in CircuitPython when USB host has write access to flash
        pass

    return saved_to_nvm or saved_to_file

# ==============================================================================
# 4. CONFIGURATION VALIDATION
# ==============================================================================

def validate_config(cfg):
    """Strictly validates configuration structure and types before applying."""
    if not isinstance(cfg, dict):
        return False

    required_modes = ["mode1", "mode2", "mode3"]
    for m in required_modes:
        if m not in cfg:
            return False
        mode_data = cfg[m]
        if not isinstance(mode_data, dict):
            return False
        buttons = mode_data.get("buttons")
        if not isinstance(buttons, list) or len(buttons) == 0 or len(buttons) > 12:
            return False

        for btn in buttons:
            if not isinstance(btn, dict):
                return False
            act_type = btn.get("type")
            if act_type not in ["combo", "single", "media", "string"]:
                return False

            if act_type == "combo":
                k = btn.get("key", "")
                if not isinstance(k, str) or k.upper() not in KEY_MAP:
                    return False
                mods = btn.get("modifiers", [])
                if not isinstance(mods, list):
                    return False
                for mod in mods:
                    if not isinstance(mod, str) or mod.upper() not in KEY_MAP:
                        return False

            elif act_type == "single":
                k = btn.get("key", "")
                if not isinstance(k, str) or k.upper() not in KEY_MAP:
                    return False

            elif act_type == "media":
                act = btn.get("action", "")
                if not isinstance(act, str) or act.upper() not in MEDIA_MAP:
                    return False

            elif act_type == "string":
                text = btn.get("text", "")
                if not isinstance(text, str) or len(text) > 256:
                    return False

    return True

# ==============================================================================
# 5. INITIALIZE HARDWARE
# ==============================================================================

# Setup Push Buttons with Internal Pull-Ups
buttons = []
for pin in BUTTON_PINS:
    btn = digitalio.DigitalInOut(pin)
    btn.direction = digitalio.Direction.INPUT
    btn.pull = digitalio.Pull.UP
    buttons.append(btn)

# Setup 3-Position Mode Switch with Internal Pull-Ups
mode_inputs = []
for pin in MODE_PINS:
    m_pin = digitalio.DigitalInOut(pin)
    m_pin.direction = digitalio.Direction.INPUT
    m_pin.pull = digitalio.Pull.UP
    mode_inputs.append(m_pin)

# Setup Status LEDs
led_g1 = digitalio.DigitalInOut(LED_GREEN_1); led_g1.direction = digitalio.Direction.OUTPUT
led_g2 = digitalio.DigitalInOut(LED_GREEN_2); led_g2.direction = digitalio.Direction.OUTPUT
led_b1 = digitalio.DigitalInOut(LED_BLUE_1); led_b1.direction = digitalio.Direction.OUTPUT
led_b2 = digitalio.DigitalInOut(LED_BLUE_2); led_b2.direction = digitalio.Direction.OUTPUT
led_r1 = digitalio.DigitalInOut(LED_RED_1); led_r1.direction = digitalio.Direction.OUTPUT
led_r2 = digitalio.DigitalInOut(LED_RED_2); led_r2.direction = digitalio.Direction.OUTPUT

green_leds = [led_g1, led_g2]
blue_leds = [led_b1, led_b2]
red_leds = [led_r1, led_r2]

# Setup USB HID
try:
    keyboard = Keyboard(usb_hid.devices)
    layout = KeyboardLayoutUS(keyboard)
    consumer_control = ConsumerControl(usb_hid.devices)
except Exception as e:
    print("USB HID not ready yet:", e)
    keyboard = None
    layout = None
    consumer_control = None

serial = usb_cdc.console
config = load_persistent_config()

# ==============================================================================
# 6. HELPER FUNCTIONS & DEBOUNCING
# ==============================================================================

def set_leds_for_mode(mode_num):
    """Activates the pair of LEDs matching the active rotary switch mode."""
    for led in green_leds + blue_leds + red_leds:
        led.value = False

    if mode_num == 1:
        for led in green_leds: led.value = True
    elif mode_num == 2:
        for led in blue_leds: led.value = True
    elif mode_num == 3:
        for led in red_leds: led.value = True

def pulse_active_leds(mode_num):
    """Tactile feedback blink on keypress."""
    active_group = green_leds if mode_num == 1 else (blue_leds if mode_num == 2 else red_leds)
    for led in active_group:
        led.value = False
    # Non-blocking or short micro pulse
    time.sleep(0.03)
    for led in active_group:
        led.value = True

def read_raw_rotary_switch():
    """Returns detected mode index (1, 2, 3) or None if between switch contacts."""
    for idx, pin in enumerate(mode_inputs):
        if not pin.value:  # Active LOW
            return idx + 1
    return None  # In-flight transition: do NOT jump to Mode 1!

def execute_action(action_def):
    """Executes the programmed key action without blocking serial."""
    if not action_def or keyboard is None:
        return

    act_type = action_def.get("type", "single")
    try:
        if act_type == "single":
            k_str = action_def.get("key", "").upper()
            if k_str in KEY_MAP:
                keyboard.send(KEY_MAP[k_str])

        elif act_type == "combo":
            modifiers = action_def.get("modifiers", [])
            k_str = action_def.get("key", "").upper()
            keys_to_press = []
            for mod in modifiers:
                m_upper = mod.upper()
                if m_upper in KEY_MAP:
                    keys_to_press.append(KEY_MAP[m_upper])
            if k_str in KEY_MAP:
                keys_to_press.append(KEY_MAP[k_str])

            if keys_to_press:
                keyboard.send(*keys_to_press)

        elif act_type == "media":
            media_action = action_def.get("action", "").upper()
            if consumer_control and media_action in MEDIA_MAP:
                consumer_control.send(MEDIA_MAP[media_action])

        elif act_type == "string":
            text = action_def.get("text", "")
            if layout and text:
                # KeyboardLayoutUS only maps standard ASCII characters (32..126, \n, \t)
                ascii_text = "".join(c for c in text if (32 <= ord(c) <= 126) or c in ("\n", "\t"))
                if ascii_text:
                    layout.write(ascii_text)

    except Exception as e:
        print("Error executing key action:", e)

def send_serial_msg(data):
    """Sends a JSON line over USB CDC to the web configurator."""
    if serial:
        try:
            line = json.dumps(data) + "\n"
            serial.write(line.encode("utf-8"))
        except Exception:
            pass

# Non-blocking USB CDC receive buffer
serial_rx_buffer = ""

def check_serial_commands():
    """Non-blocking check for incoming commands from the Web Configurator."""
    global config, serial_rx_buffer
    if not serial or not serial.in_waiting:
        return

    try:
        # Read only available bytes without blocking
        chunk = serial.read(serial.in_waiting)
        if chunk:
            serial_rx_buffer += chunk.decode("utf-8", "ignore")
            # Safety limit against buffer bloat if garbage data arrives
            if len(serial_rx_buffer) > 4096:
                serial_rx_buffer = ""

        if "\n" not in serial_rx_buffer:
            return

        lines = serial_rx_buffer.split("\n")
        serial_rx_buffer = lines.pop()  # Retain trailing partial command

        for raw_line in lines:
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            cmd = json.loads(raw_line)
            action = cmd.get("action")

            if action == "PING":
                send_serial_msg({
                    "response": "PONG",
                    "device": "Raspberry Pi Pico MacroPad",
                    "current_mode": current_mode,
                    "button_count": len(buttons)
                })

            elif action == "GET_CONFIG":
                send_serial_msg({
                    "response": "CONFIG",
                    "config": config,
                    "current_mode": current_mode
                })

            elif action == "SET_CONFIG":
                new_cfg = cmd.get("config")
                if validate_config(new_cfg):
                    config = new_cfg
                    saved = save_persistent_config(config)
                    send_serial_msg({
                        "response": "CONFIG_SAVED",
                        "status": "ok",
                        "persistent": saved
                    })
                    # Visual confirmation flash
                    for _ in range(3):
                        for led in green_leds + blue_leds + red_leds: led.value = True
                        time.sleep(0.06)
                        for led in green_leds + blue_leds + red_leds: led.value = False
                        time.sleep(0.06)
                    set_leds_for_mode(current_mode)
                else:
                    send_serial_msg({
                        "response": "ERROR",
                        "message": "Invalid configuration structure or unsupported keycode"
                    })

    except Exception as err:
        send_serial_msg({"response": "ERROR", "message": str(err)})

# ==============================================================================
# 7. MAIN LOOP (NON-BLOCKING WITH TIMESTAMP DEBOUNCING)
# ==============================================================================

DEBOUNCE_TIME_MS = 0.040  # 40 milliseconds button debounce
ROTARY_STABLE_SAMPLES = 3  # Must read same position 3 consecutive times to avoid transition flicker

current_mode = read_raw_rotary_switch() or 1
candidate_mode = current_mode
rotary_sample_count = 0
set_leds_for_mode(current_mode)

# State tracking
last_button_phys_state = [True] * len(buttons)  # True = unpressed (Pull-up)
last_button_press_time = [0.0] * len(buttons)

print("Macro Keyboard Ready. Active Mode:", current_mode)

while True:
    now = time.monotonic()

    # 1. Process Web Serial commands
    check_serial_commands()

    # 2. Rotary Switch with glitch-free sample filtering
    detected_mode = read_raw_rotary_switch()
    if detected_mode is not None:
        if detected_mode == candidate_mode:
            rotary_sample_count += 1
            if rotary_sample_count >= ROTARY_STABLE_SAMPLES and current_mode != candidate_mode:
                current_mode = candidate_mode
                set_leds_for_mode(current_mode)
                send_serial_msg({"event": "MODE_CHANGED", "mode": current_mode})
        else:
            candidate_mode = detected_mode
            rotary_sample_count = 1
    else:
        # In-flight between rotary contacts: reset counter and hold previous mode
        rotary_sample_count = 0

    # 3. Read Push Buttons with timestamp debouncing
    for i, btn in enumerate(buttons):
        curr_state = btn.value  # False = Pressed (pulled to GND), True = Released

        if curr_state != last_button_phys_state[i]:
            if (now - last_button_press_time[i]) >= DEBOUNCE_TIME_MS:
                last_button_press_time[i] = now
                last_button_phys_state[i] = curr_state

                if not curr_state:
                    # Fresh keypress detected!
                    pulse_active_leds(current_mode)

                    # Notify Web Configurator in real time
                    send_serial_msg({
                        "event": "BUTTON_PRESSED",
                        "button_id": i,
                        "mode": current_mode
                    })

                    # Execute configured action for current mode & button
                    mode_key = f"mode{current_mode}"
                    mode_data = config.get(mode_key, {})
                    mode_buttons = mode_data.get("buttons", [])

                    if i < len(mode_buttons):
                        execute_action(mode_buttons[i])

    time.sleep(0.005)

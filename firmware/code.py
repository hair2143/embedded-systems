"""
Raspberry Pi Pico (RP2040) Macro Keyboard Firmware
CircuitPython 8.x / 9.x

Features:
- Full USB HID Keyboard & Consumer Media Control
- USB Serial (CDC) interface for real-time Web Configurator sync
- 3-Position Rotary Switcher for Layer / Profile selection (Modes 1, 2, 3)
- 6 Status LEDs (2 Green for Mode 1, 2 Blue for Mode 2, 2 Red for Mode 3) with keypress pulsing
- Dynamic JSON configuration storage (flash or memory)
- Real-time keypress broadcasting back to the Web Configurator
"""

import time
import json
import board
import digitalio
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
# Connect one side to GPIO, other side to GND
BUTTON_PINS = [board.GP2, board.GP3, board.GP4, board.GP5]

# 3-Position Rotary Selector Pins (GP6, GP7, GP8)
# Connect common pin to GND, selector positions to GPIO
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
# 2. DEFAULT PROFILES & KEYCODE MAPPINGS
# ==============================================================================

# Map friendly string names to Keycode values
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

# Consumer media controls
MEDIA_MAP = {
    "MUTE": ConsumerControlCode.MUTE,
    "VOLUME_UP": ConsumerControlCode.VOLUME_INCREMENT,
    "VOLUME_DOWN": ConsumerControlCode.VOLUME_DECREMENT,
    "PLAY_PAUSE": ConsumerControlCode.PLAY_PAUSE,
    "STOP": ConsumerControlCode.STOP,
    "NEXT_TRACK": ConsumerControlCode.SCAN_NEXT_TRACK,
    "PREV_TRACK": ConsumerControlCode.SCAN_PREVIOUS_TRACK,
}

# Default 3 Modes / Profiles
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

config = DEFAULT_CONFIG

# ==============================================================================
# 3. INITIALIZE HARDWARE
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

# Setup LEDs
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

# Serial interface for Web Configurator
serial = usb_cdc.console

# ==============================================================================
# 4. HELPER FUNCTIONS
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
    """Briefly blinks active LEDs to provide tactile visual feedback on keypress."""
    active_group = green_leds if mode_num == 1 else (blue_leds if mode_num == 2 else red_leds)
    for led in active_group:
        led.value = False
    time.sleep(0.04)
    for led in active_group:
        led.value = True

def get_current_mode():
    """Reads 3-position selector switch (pin pulled LOW = active position)."""
    for idx, pin in enumerate(mode_inputs):
        if not pin.value:  # Low = active switch position
            return idx + 1
    # Fallback to Mode 1 if switch is in transit or disconnected
    return 1

def execute_action(action_def):
    """Executes the programmed action (key combo, media key, or string typing)."""
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
                if mod.upper() in KEY_MAP:
                    keys_to_press.append(KEY_MAP[mod.upper()])
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
                layout.write(text)

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

def check_serial_commands():
    """Checks for incoming configuration commands from the Web Configurator."""
    global config
    if not serial or not serial.in_waiting:
        return

    try:
        raw_line = serial.readline().decode("utf-8").strip()
        if not raw_line:
            return

        cmd = json.loads(raw_line)
        action = cmd.get("action")

        if action == "PING":
            # Handshake with Web Configurator
            send_serial_msg({
                "response": "PONG",
                "device": "Raspberry Pi Pico MacroPad",
                "current_mode": current_mode,
                "button_count": len(buttons)
            })

        elif action == "GET_CONFIG":
            # Web app requests current configuration
            send_serial_msg({
                "response": "CONFIG",
                "config": config,
                "current_mode": current_mode
            })

        elif action == "SET_CONFIG":
            # Web app sends new configuration
            new_cfg = cmd.get("config")
            if new_cfg:
                config = new_cfg
                send_serial_msg({"response": "CONFIG_SAVED", "status": "ok"})
                # Flash all LEDs to confirm save
                for _ in range(3):
                    for led in green_leds + blue_leds + red_leds: led.value = True
                    time.sleep(0.08)
                    for led in green_leds + blue_leds + red_leds: led.value = False
                    time.sleep(0.08)
                set_leds_for_mode(current_mode)

    except Exception as err:
        send_serial_msg({"response": "ERROR", "message": str(err)})

# ==============================================================================
# 5. MAIN LOOP
# ==============================================================================

# Button state tracking (for debouncing)
last_button_states = [True] * len(buttons)  # True = unpressed (Pull-up)
current_mode = get_current_mode()
set_leds_for_mode(current_mode)

print("Macro Keyboard Ready. Active Mode:", current_mode)

while True:
    # 1. Check for commands from the Web Configurator
    check_serial_commands()

    # 2. Check 3-position rotary mode switch
    new_mode = get_current_mode()
    if new_mode != current_mode:
        current_mode = new_mode
        set_leds_for_mode(current_mode)
        send_serial_msg({"event": "MODE_CHANGED", "mode": current_mode})
        time.sleep(0.05)

    # 3. Read and debounce Push Buttons
    for i, btn in enumerate(buttons):
        curr_state = btn.value  # False = Pressed (to GND), True = Released

        if not curr_state and last_button_states[i]:
            # Button just pressed!
            pulse_active_leds(current_mode)

            # Notify Web Configurator in real-time
            send_serial_msg({
                "event": "BUTTON_PRESSED",
                "button_id": i,
                "mode": current_mode
            })

            # Fetch action for current mode and button index
            mode_key = f"mode{current_mode}"
            mode_data = config.get(mode_key, {})
            mode_buttons = mode_data.get("buttons", [])

            if i < len(mode_buttons):
                execute_action(mode_buttons[i])

            # Small debounce delay
            time.sleep(0.02)

        last_button_states[i] = curr_state

    time.sleep(0.01)

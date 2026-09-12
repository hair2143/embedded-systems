# Breadboard Wiring Guide for Pico Macro Keyboard

This guide shows how to wire your **Raspberry Pi Pico (RP2040)**, **push buttons**, **3-position rotary switch**, and **6 LEDs (2 Green, 2 Blue, 2 Red)** on a breadboard.

---

## 1. Raspberry Pi Pico Pinout Reference

```
                   ┌──────────┐
      GP0 (Pin 1)  │ [ ]  [ ] │  VBUS (Pin 40 - 5V USB)
      GP1 (Pin 2)  │ [ ]  [ ] │  VSYS (Pin 39)
      GND (Pin 3)  │ [x]  [ ] │  GND  (Pin 38)
 [Btn 1] GP2 (Pin 4)  │ [x]  [ ] │  3V3_EN (Pin 37)
 [Btn 2] GP3 (Pin 5)  │ [x]  [ ] │  3V3(OUT) (Pin 36)
 [Btn 3] GP4 (Pin 6)  │ [x]  [ ] │  ADC_VREF (Pin 35)
 [Btn 4] GP5 (Pin 7)  │ [x]  [ ] │  GP28 (Pin 34)
      GND (Pin 8)  │ [x]  [ ] │  GND  (Pin 33)
 [Rot 1] GP6 (Pin 9)  │ [x]  [ ] │  GP27 (Pin 32)
 [Rot 2] GP7 (Pin 10) │ [x]  [ ] │  GP26 (Pin 31)
 [Rot 3] GP8 (Pin 11) │ [x]  [ ] │  RUN  (Pin 30)
      GP9 (Pin 12) │ [ ]  [ ] │  GP22 (Pin 29)
      GND (Pin 13) │ [x]  [x] │  GND  (Pin 28)
     GP10 (Pin 14) │ [ ]  [ ] │  GP21 (Pin 27)
     GP11 (Pin 15) │ [ ]  [ ] │  GP20 (Pin 26)
     GP12 (Pin 16) │ [ ]  [x] │  GP19 (Pin 25) [Red LED 2]
     GP13 (Pin 17) │ [ ]  [x] │  GP18 (Pin 24) [Red LED 1]
      GND (Pin 18) │ [x]  [x] │  GND  (Pin 23)
[Grn LED 1] GP14 (Pin 19) │ [x]  [x] │  GP17 (Pin 22) [Blue LED 2]
[Grn LED 2] GP15 (Pin 20) │ [x]  [x] │  GP16 (Pin 21) [Blue LED 1]
                   └──────────┘
```

---

## 2. Push Buttons Wiring (4 Buttons)

Each button connects between a GPIO pin and **GND** (The firmware enables the RP2040's internal pull-up resistor, so **no external pull-up resistors are needed!**):

* **Button 1**: Connect one terminal to **GP2 (Pin 4)**, the other terminal to **GND (Pin 3 or 8)**.
* **Button 2**: Connect one terminal to **GP3 (Pin 5)**, the other terminal to **GND (Pin 8)**.
* **Button 3**: Connect one terminal to **GP4 (Pin 6)**, the other terminal to **GND (Pin 8)**.
* **Button 4**: Connect one terminal to **GP5 (Pin 7)**, the other terminal to **GND (Pin 8)**.

---

## 3. 3-Position Rotary Switch Wiring (Mode / Profile Selector)

The 3-position rotary switch has **1 Common pin** and **3 Terminal pins**:

* **Common Pin**: Connect to **GND (Pin 8 or Pin 13)**.
* **Terminal 1 (Position 1 - Dev Mode)**: Connect to **GP6 (Pin 9)**.
* **Terminal 2 (Position 2 - Media Mode)**: Connect to **GP7 (Pin 10)**.
* **Terminal 3 (Position 3 - Quick Tools Mode)**: Connect to **GP8 (Pin 11)**.

When you turn the switch, it grounds the selected GPIO pin, signaling the Pico to switch active layer and LEDs!

---

## 4. Status LEDs Wiring (6 LEDs)

Always connect a current-limiting resistor ($220\Omega$ or $330\Omega$) in series with each LED.

* **Long leg of LED** = Anode (+)
* **Short leg of LED** = Cathode (-)

### Mode 1 - Green LEDs
1. **Green LED 1**: **GP14 (Pin 19)** $\to$ Resistor ($220\Omega$) $\to$ Anode (+); Cathode (-) $\to$ **GND (Pin 18)**
2. **Green LED 2**: **GP15 (Pin 20)** $\to$ Resistor ($220\Omega$) $\to$ Anode (+); Cathode (-) $\to$ **GND (Pin 18)**

### Mode 2 - Blue LEDs
3. **Blue LED 1**: **GP16 (Pin 21)** $\to$ Resistor ($220\Omega$) $\to$ Anode (+); Cathode (-) $\to$ **GND (Pin 23)**
4. **Blue LED 2**: **GP17 (Pin 22)** $\to$ Resistor ($220\Omega$) $\to$ Anode (+); Cathode (-) $\to$ **GND (Pin 23)**

### Mode 3 - Red LEDs
5. **Red LED 1**: **GP18 (Pin 24)** $\to$ Resistor ($220\Omega$) $\to$ Anode (+); Cathode (-) $\to$ **GND (Pin 23)**
6. **Red LED 2**: **GP19 (Pin 25)** $\to$ Resistor ($220\Omega$) $\to$ Anode (+); Cathode (-) $\to$ **GND (Pin 28)**

---

## 5. Summary Wiring Checklist

| Component | Connected To | Grounded To | Function |
| :--- | :--- | :--- | :--- |
| Button 1 | **GP2** (Pin 4) | GND | Custom Action 1 |
| Button 2 | **GP3** (Pin 5) | GND | Custom Action 2 |
| Button 3 | **GP4** (Pin 6) | GND | Custom Action 3 |
| Button 4 | **GP5** (Pin 7) | GND | Custom Action 4 |
| Rotary Pos 1 | **GP6** (Pin 9) | GND (Common) | Mode 1 (Dev) |
| Rotary Pos 2 | **GP7** (Pin 10) | GND (Common) | Mode 2 (Media) |
| Rotary Pos 3 | **GP8** (Pin 11) | GND (Common) | Mode 3 (Tools) |
| Green LEDs (2x) | **GP14 & GP15** (with $220\Omega$) | GND | Lights when Mode 1 active |
| Blue LEDs (2x) | **GP16 & GP17** (with $220\Omega$) | GND | Lights when Mode 2 active |
| Red LEDs (2x) | **GP18 & GP19** (with $220\Omega$) | GND | Lights when Mode 3 active |

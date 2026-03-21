
# Anti Theft Weight Verification System

A hardware + software combined college project that prevents
theft at supermarket self checkout counters using weight
verification at the exit gate.

## Tech Stack
- Python 3 + Tkinter (GUI)
- SQLite (Database)
- Arduino Uno (Hardware)
- HX711 Load Cell Amplifier
- LCD 16x2 I2C Display
- Active Buzzer + LEDs
- ReportLab (PDF Bill Generation)
- PySerial (Arduino Communication)

## Hardware Components
- Arduino Uno
- HX711 + Load Cell (5kg)
- LCD 16x2 with I2C module
- Green LED + Red LED
- Active Buzzer
- 2x 220 ohm Resistors
- Breadboard + Jumper Wires

## How to Run

### Software Setup
pip install reportlab pillow pyserial
python main_app.py

### Arduino Setup
1. Open arduino_hardware/antitheft_hardware.ino
2. Install libraries: HX711, LiquidCrystal I2C
3. Upload to Arduino Uno

## Project Flow
1. Customer scans products at billing counter
2. System stores total weight in database
3. At exit gate customer places bag on load cell
4. If weight matches - GREEN LED + LCD shows MATCHED
5. If weight mismatch - RED LED + BUZZER + LCD shows ALERT

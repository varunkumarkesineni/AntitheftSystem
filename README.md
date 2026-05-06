<div align="center">

#  Anti-Theft Weight Verification System

### Hardware + Software Combined College Project

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Arduino](https://img.shields.io/badge/Arduino-Uno-00979D?style=for-the-badge&logo=arduino&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen?style=for-the-badge)

> A smart anti-theft system for supermarket self-checkout counters that verifies customer bag weight at the exit gate against the billed weight stored in the database — triggering alerts for any mismatch.

**College Project | Hyderabad, Telangana | 2026**

---

[🎯 Features](#-features) • [🛠️ Tech Stack](#️-tech-stack) • [⚙️ Hardware](#️-hardware-components) • [🚀 Setup](#-software-setup) • [📸 Flow](#-system-flow) • [🔌 Wiring](#-hardware-wiring)

</div>

---

## 🎯 Features

| Feature | Description |
|---|---|
| 🛒 Self-Checkout Billing | Scan barcodes → auto-fetch product → build cart → generate PDF bill |
| ⚖️ Weight Verification | Compare actual bag weight with billed weight at exit gate |
| 🔌 Auto Mode | Arduino + HX711 load cell reads weight automatically via Serial |
| ✏️ Manual Mode | Enter weight manually for demo or testing without hardware |
| 🖥️ LCD Display | Real-time status shown on 16x2 LCD display |
| 🟢🔴 LED Indicators | Green LED for pass, Red LED for mismatch alert |
| 🔊 Buzzer Alert | Active buzzer triggers on weight mismatch |
| 📄 PDF Bill | Professional bill generated with itemized list and expected weight |
| 🗄️ SQLite Database | All products, sessions and verification logs stored locally |
| 📊 Verification Logs | Complete history of all exit gate verifications |

---

## 🛠️ Tech Stack

### Software
| Technology | Purpose |
|---|---|
| Python 3.10+ | Main application language |
| Tkinter | GUI framework |
| SQLite | Local database |
| ReportLab | PDF bill generation |
| PySerial | Arduino serial communication |
| Pillow | Image processing |

### Hardware
| Component | Purpose |
|---|---|
| Arduino Uno | Microcontroller |
| HX711 Module | Load cell amplifier |
| Load Cell 5kg | Weight measurement |
| LCD 16x2 I2C | Display output |
| Green LED | Pass indicator |
| Red LED | Alert indicator |
| Active Buzzer | Audio alert |
| Breadboard + Wires | Circuit connections |
| 2× 220Ω Resistors | LED current limiting |

---

## ⚙️ Hardware Components

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────┐
│  Load Cell  │────▶│    HX711    │────▶│   Arduino Uno   │
│   (5kg)     │     │  Amplifier  │     │                 │
└─────────────┘     └─────────────┘     │  Pin 2  → SCK   │
                                        │  Pin 3  → DT    │
┌─────────────┐                         │  Pin 8  → LED G │
│ LCD 16x2    │◀───────────────────────│  Pin 9  → LED R │
│  (I2C)      │     SDA → A4           │  Pin 10 → Buzz  │
│             │     SCL → A5           │  A4     → SDA   │
└─────────────┘                         │  A5     → SCL   │
                                        └─────────────────┘
┌──────────┐  ┌──────────┐  ┌──────────┐        │
│ Green LED│  │  Red LED │  │  Buzzer  │        │ USB Serial
│ Pin8+220Ω│  │ Pin9+220Ω│  │  Pin 10  │        ▼
└──────────┘  └──────────┘  └──────────┘   ┌──────────┐
                                            │    PC    │
                                            │  Python  │
                                            │   App    │
                                            └──────────┘
```

---

## 🔌 Hardware Wiring

### Load Cell → HX711
| Load Cell Wire | HX711 Pin |
|---|---|
| Red | E+ |
| Black | E- |
| White | A+ |
| Green | A- |

### HX711 → Arduino
| HX711 Pin | Arduino Pin |
|---|---|
| VCC | 5V |
| GND | GND |
| DT | Pin 3 |
| SCK | Pin 2 |

### LCD 16x2 I2C → Arduino
| LCD Pin | Arduino Pin |
|---|---|
| VCC | 5V |
| GND | GND |
| SDA | A4 |
| SCL | A5 |

### LEDs + Buzzer → Arduino
```
Pin 8  → 220Ω → Green LED (+) → Green LED (-) → GND
Pin 9  → 220Ω → Red LED (+)   → Red LED (-)   → GND
Pin 10 → Buzzer (+) long leg  |  Buzzer (-) → GND
```

> 💡 All components share common GND through breadboard GND rail

---

## 🗄️ Database Schema

```sql
products          -- 20 pre-loaded products with barcode, price, weight
sessions          -- each customer billing session
session_items     -- individual scanned items per session
verification_logs -- exit gate weight check history
```

### Pre-Loaded Products (20 items)
| Barcode | Product | Price | Weight |
|---|---|---|---|
| 8901030874023 | Amul Full Cream Milk 500ml | ₹28 | 520g |
| 8901719114045 | Parle-G Original 100g | ₹10 | 100g |
| 8901764100027 | Maggi 2-Min Noodles 70g | ₹14 | 70g |
| 8901058870015 | Bisleri Water Bottle 1L | ₹20 | 1050g |
| 8901396030413 | Coca-Cola 500ml | ₹40 | 540g |
| 8901491500023 | Britannia Good Day 200g | ₹30 | 200g |
| 8901058003218 | Lays Classic Salted 45g | ₹20 | 45g |
| 8901764502019 | KitKat Chocolate 37g | ₹30 | 37g |
| 8906003480034 | Aashirvaad Atta 1kg | ₹55 | 1050g |
| 8906017400012 | Tata Salt 1kg | ₹24 | 1020g |
| *...and 10 more* | | | |

---

## 🚀 Software Setup

### Prerequisites
- Python 3.10 or higher
- pip package manager

### Installation

**Step 1 — Clone the repository**
```bash
git clone https://github.com/varunkumarkesineni/AntitheftSystem.git
cd AntitheftSystem
```

**Step 2 — Install required libraries**
```bash
pip install reportlab pillow pyserial
```

**Step 3 — Run the application**
```bash
python main_app.py
```

> The database (`antitheft.db`) and `bills/` folder are created automatically on first run with all 20 products pre-loaded.

---

## 🔧 Arduino Setup

**Step 1 — Install Arduino IDE**
Download from [https://arduino.cc/en/software](https://arduino.cc/en/software)

**Step 2 — Install Required Libraries**

Open Arduino IDE → Tools → Manage Libraries → Search and install:
- `HX711` by Bogdan Necula
- `LiquidCrystal I2C` by Frank de Bruijn

**Step 3 — Upload Code**
- Open `arduino_hardware/antitheft_hardware.ino`
- Select Board: `Tools → Board → Arduino Uno`
- Select Port: `Tools → Port → COM3` (or your port)
- Click Upload

**Step 4 — Calibrate Load Cell**

Open Serial Monitor (baud: 9600) and type:
```
TARE        ← zeros the scale
READWEIGHT  ← reads current weight
VERIFY:520  ← tests verification with 520g expected
```

---

## 📸 System Flow

```
BILLING COUNTER                    EXIT GATE
─────────────────                  ──────────────────────
Customer scans barcode             Session ID loaded
       ↓                                  ↓
Product fetched from DB            Expected weight loaded
       ↓                                  ↓
Added to cart                      Customer places bag
       ↓                            on load cell
Total weight calculated                   ↓
       ↓                           Arduino reads weight
Bill generated (PDF)                      ↓
       ↓                           Compare actual vs expected
Session ID printed                        ↓
       ↓                    ┌─────────────────────────┐
Customer proceeds           │  |diff| ≤ 50g ?         │
to exit gate                │  YES → MATCHED ✅        │
                            │       Green LED ON       │
                            │       LCD: MATCHED       │
                            │                         │
                            │  NO  → MISMATCH ❌       │
                            │       Red LED ON         │
                            │       Buzzer beeps       │
                            │       LCD: ALERT!        │
                            └─────────────────────────┘
```

---

## 📁 Project Structure

```
AntitheftSystem/
│
├── main_app.py                 # Main GUI application
├── database_setup.py           # Database schema + product seeding
├── antitheft.db                # SQLite database (auto-created)
│
├── arduino_hardware/
│   └── antitheft_hardware.ino  # Arduino code
│
├── bills/                      # Generated PDF bills (auto-created)
│
└── README.md                   # Project documentation
```

---

## 💼 Business Model

| Aspect | Details |
|---|---|
| Target Market | D-Mart, Reliance Fresh, Big Bazaar, Airport retail |
| Hardware Cost | ₹8,000 – ₹15,000 per exit gate |
| Software SaaS | ₹2,000 – ₹5,000 per month |
| Shrinkage Loss | 2–3% of revenue in Indian retail |
| ROI for Store | Break-even in under 1 month |

---

## 👨‍💻 Team

**Project by:** Varun Kumar Kesineni

**Institution:** CMR College Of Engineering & Technology — Hyderabad,Telangana,Ind

**Year:** 2025-2026

---

## 📄 License

This project is licensed under the MIT License.

---

<div align="center">

### ⭐ If you found this project useful, please give it a star!

**Made with ❤️ in Hyderabad, India**

</div>

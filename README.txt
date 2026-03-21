=================================================================
  ANTI-THEFT WEIGHT VERIFICATION SYSTEM
  College Project — Hardware + Software Combined
  Python + SQLite + Arduino + HX711 + LCD + LED + Buzzer
=================================================================

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PROJECT OVERVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
When customers self-checkout at supermarkets (D-Mart, Reliance),
they scan items and pack into carry bags. Some may skip scanning.
Our system prevents theft by verifying bag weight at the exit gate
against the expected weight stored in the database after billing.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  HARDWARE COMPONENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  1. Arduino Uno / Mega
  2. HX711 Load Cell Amplifier Module
  3. Load Cell (5kg or 10kg rated)
  4. LCD 16x2 Display with I2C Module
  5. Red LED (5mm)
  6. Green LED (5mm)
  7. Active Buzzer
  8. 2× 220Ω Resistors (for LEDs)
  9. Jumper wires + Breadboard
  10. USB Cable (Arduino ↔ PC)
  11. PC / Raspberry Pi running Python

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  HARDWARE WIRING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  HX711 → Arduino:
    VCC  → 5V
    GND  → GND
    DT   → Pin 3
    SCK  → Pin 2

  HX711 → Load Cell:
    E+   → Load Cell Red
    E-   → Load Cell Black
    A+   → Load Cell White
    A-   → Load Cell Green

  LCD I2C → Arduino:
    VCC  → 5V
    GND  → GND
    SDA  → A4
    SCL  → A5

  Green LED → Pin 8 → 220Ω → GND
  Red LED   → Pin 9 → 220Ω → GND
  Buzzer(+) → Pin 10, Buzzer(-) → GND

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  SOFTWARE SETUP (PC)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Requirements: Python 3.9+

  Install dependencies:
    pip install reportlab pillow

  For MySQL (optional, SQLite is default):
    pip install mysql-connector-python

  Run the app:
    python main_app.py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  DATABASE SCHEMA (SQLite: antitheft.db)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  TABLE: products
    barcode      TEXT  PRIMARY KEY
    name         TEXT
    price        REAL
    weight_g     REAL    ← weight of product in grams
    category     TEXT
    brand        TEXT
    unit         TEXT

  TABLE: sessions
    session_id      TEXT PRIMARY KEY
    created_at      DATETIME
    total_price     REAL
    total_weight_g  REAL    ← sum of all item weights
    item_count      INTEGER
    status          TEXT    (active/billed/verified/flagged)

  TABLE: session_items
    id           INTEGER PK
    session_id   TEXT FK
    barcode      TEXT FK
    product_name TEXT
    qty          INTEGER
    price_each   REAL
    weight_g     REAL

  TABLE: verification_logs
    id              INTEGER PK
    session_id      TEXT FK
    expected_weight REAL
    actual_weight   REAL
    difference_g    REAL
    result          TEXT    (MATCHED/MISMATCH)
    verified_at     DATETIME

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PRE-LOADED PRODUCTS (20 items)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Barcode            Product                       Price    Weight
  ─────────────────────────────────────────────────────────────
  8901030874023   Amul Full Cream Milk 500ml      ₹28    520g
  8901030559565   Amul Butter 100g                ₹55    110g
  8901491500023   Britannia Good Day Biscuits     ₹30    200g
  8901719114045   Parle-G Original 100g           ₹10    100g
  8901764100027   Maggi 2-Min Noodles             ₹14     70g
  8901058870015   Bisleri Water 1L                ₹20   1050g
  8901396030413   Coca-Cola 500ml                 ₹40    540g
  8901058003218   Lay's Classic Chips 45g         ₹20     45g
  8901030591441   Amul Dahi 400g                  ₹44    420g
  8901764502019   KitKat Chocolate                ₹30     37g
  8901491100194   Britannia Marie Gold 250g       ₹25    250g
  8906003480034   Aashirvaad Atta 1kg             ₹55   1050g
  8901764102137   Munch Chocolate Bar             ₹10      9.6g
  8901491700169   Bourbon Biscuits 150g           ₹25    150g
  8901030560516   Amul Cheese Slices 200g        ₹100    210g
  8906017400012   Tata Salt 1kg                   ₹24   1020g
  8901764108665   Milkmaid 200g                   ₹60    200g
  8901058038258   Pepsi 600ml                     ₹40    640g
  8901396080110   Sprite 300ml                    ₹20    330g
  8906017750015   Tata Tea Premium 100g           ₹55    110g

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  COMPLETE FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  STEP 1 — Customer scans products at self-checkout:
    → Barcode reader sends barcode to PC
    → Software looks up product in DB
    → Item added to cart (price + weight stored)
    → Session accumulated

  STEP 2 — Bill Generation:
    → Customer clicks "Generate Bill"
    → PDF bill created with total price + expected bag weight
    → Session status → "billed"
    → Session ID printed on bill

  STEP 3 — Exit Gate Verification:
    → Customer proceeds to exit gate
    → Security scans Session ID from bill
    → Expected weight loaded from DB
    → Customer places carry bag on Load Cell

  STEP 4 — Hardware Verification:
    → Arduino reads Load Cell via HX711
    → Weight sent to PC via Serial
    → PC compares: |actual - expected| ≤ 50g ?

  STEP 5 — Result:
    MATCHED  → Green LED ON + LCD "MATCHED" + Gate opens
    MISMATCH → Red LED ON + Buzzer beeps + LCD "MISMATCH" + Alert

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  BUSINESS MODEL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Target Customers:
    • D-Mart, Reliance Fresh, Big Bazaar, Spencer's
    • Airport retail stores
    • Any self-checkout enabled supermarket

  Revenue Model:
    • One-time hardware kit sale: ₹8,000–₹15,000 per gate
    • SaaS subscription for software: ₹2,000–₹5,000/month
    • Installation + maintenance contract

  Cost Savings for Store:
    • Shrinkage (theft loss) in Indian retail: ~2–3% of revenue
    • A ₹1 crore/month store loses ₹2–3 lakh to theft
    • Our system can reduce this by 70–80%

  ROI for Store:
    • System cost: ~₹50,000 per exit gate (hardware + 1yr software)
    • Monthly savings: ₹1.5–2 lakh
    • Break-even: < 1 month

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PROJECT FILES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  antitheft_system/
  ├── main_app.py               ← Main GUI application (run this)
  ├── database_setup.py         ← DB schema + product seeding
  ├── antitheft.db              ← SQLite database (auto-created)
  ├── bills/                    ← Generated PDF bills
  ├── arduino_hardware/
  │   └── antitheft_hardware.ino ← Arduino code
  └── README.txt                ← This file

=================================================================

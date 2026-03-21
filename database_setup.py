"""
=============================================================
  ANTI-THEFT WEIGHT VERIFICATION SYSTEM
  Database Setup & Initialization Script
  College Project | Hardware + Software Integration
=============================================================
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "antitheft.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    # ── Products Table ──────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            barcode     TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            price       REAL NOT NULL,
            weight_g    REAL NOT NULL,      -- weight in grams
            category    TEXT,
            brand       TEXT,
            unit        TEXT DEFAULT 'piece'
        )
    """)

    # ── Sessions / Transactions Table ───────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id      TEXT PRIMARY KEY,
            created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
            total_price     REAL DEFAULT 0,
            total_weight_g  REAL DEFAULT 0,
            item_count      INTEGER DEFAULT 0,
            status          TEXT DEFAULT 'active'  -- active | billed | verified | flagged
        )
    """)

    # ── Session Items Table ──────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS session_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  TEXT NOT NULL,
            barcode     TEXT NOT NULL,
            product_name TEXT,
            qty         INTEGER DEFAULT 1,
            price_each  REAL,
            weight_g    REAL,
            scanned_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id),
            FOREIGN KEY (barcode) REFERENCES products(barcode)
        )
    """)

    # ── Exit Verification Logs ───────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verification_logs (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id      TEXT NOT NULL,
            expected_weight REAL,
            actual_weight   REAL,
            difference_g    REAL,
            result          TEXT,   -- MATCHED | MISMATCH
            verified_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
            notes           TEXT
        )
    """)

    conn.commit()

    # ── Insert Pre-Loaded Products ───────────────────────────
    products = [
        # (barcode, name, price, weight_g, category, brand, unit)
        ("8901030874023", "Amul Full Cream Milk 500ml",     28.0,   520.0,  "Dairy",       "Amul",      "500ml"),
        ("8901030559565", "Amul Butter 100g",                55.0,   110.0,  "Dairy",       "Amul",      "100g"),
        ("8901491500023", "Britannia Good Day Biscuits",     30.0,   200.0,  "Snacks",      "Britannia", "200g"),
        ("8901719114045", "Parle-G Original Biscuits",       10.0,   100.0,  "Snacks",      "Parle",     "100g"),
        ("8901764100027", "Maggi 2-Min Noodles",             14.0,   70.0,   "Instant Food","Nestle",    "70g"),
        ("8901058870015", "Bisleri Water Bottle 1L",         20.0,   1050.0, "Beverages",   "Bisleri",   "1L"),
        ("8901396030413", "Coca-Cola 500ml",                 40.0,   540.0,  "Beverages",   "Coca-Cola", "500ml"),
        ("8901058003218", "Lay's Classic Salted Chips",      20.0,   45.0,   "Snacks",      "PepsiCo",   "45g"),
        ("8901030591441", "Amul Dahi (Curd) 400g",           44.0,   420.0,  "Dairy",       "Amul",      "400g"),
        ("8901764502019", "KitKat Chocolate",                30.0,   37.0,   "Confectionery","Nestle",   "37g"),
        ("8901491100194", "Britannia Marie Gold",            25.0,   250.0,  "Snacks",      "Britannia", "250g"),
        ("8906003480034", "Aashirvaad Atta 1kg",             55.0,   1050.0, "Grocery",     "ITC",       "1kg"),
        ("8901764102137", "Munch Chocolate Bar",             10.0,   9.6,    "Confectionery","Nestle",   "9.6g"),
        ("8901491700169", "Bourbon Biscuits 150g",           25.0,   150.0,  "Snacks",      "Britannia", "150g"),
        ("8901030560516", "Amul Cheese Slices 200g",        100.0,   210.0,  "Dairy",       "Amul",      "200g"),
        ("8906017400012", "Tata Salt 1kg",                   24.0,   1020.0, "Grocery",     "Tata",      "1kg"),
        ("8901764108665", "Milkmaid Condensed Milk 200g",    60.0,   200.0,  "Dairy",       "Nestle",    "200g"),
        ("8901058038258", "Pepsi 600ml",                     40.0,   640.0,  "Beverages",   "PepsiCo",   "600ml"),
        ("8901396080110", "Sprite 300ml",                    20.0,   330.0,  "Beverages",   "Coca-Cola", "300ml"),
        ("8906017750015", "Tata Tea Premium 100g",           55.0,   110.0,  "Beverages",   "Tata",      "100g"),
    ]

    cursor.executemany("""
        INSERT OR IGNORE INTO products
        (barcode, name, price, weight_g, category, brand, unit)
        VALUES (?,?,?,?,?,?,?)
    """, products)

    conn.commit()
    conn.close()
    print(f"[DB] Database initialized at: {DB_PATH}")
    print(f"[DB] {len(products)} products pre-loaded.")

if __name__ == "__main__":
    init_database()

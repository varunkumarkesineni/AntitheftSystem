"""
=============================================================
  ANTI-THEFT WEIGHT VERIFICATION SYSTEM
  Main Application — Billing + Exit Gate Verification
  College Project | Python + SQLite + Tkinter + PySerial
=============================================================
  Hardware Simulated:
    - Barcode Scanner  → Entry field (keyboard/USB scanner)
    - Load Cell        → Auto (Arduino Serial) OR Manual entry
    - LCD Display      → Green/Red panel in GUI
    - Buzzer           → Simulated flash + sound
    - LED Indicators   → Colored status lamps in GUI
=============================================================
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3, os, uuid, datetime, threading, time
try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm

# ── Config ──────────────────────────────────────────────────
DB_PATH    = os.path.join(os.path.dirname(__file__), "antitheft.db")
STORE_NAME = "SmartMart Superstore"
STORE_ADDR = "Plot 12, Hitech City, Hyderabad - 500081"
TOLERANCE  = 10       # 10g
BAUD_RATE  = 9600
BILL_DIR   = os.path.join(os.path.dirname(__file__), "bills")
os.makedirs(BILL_DIR, exist_ok=True)

# ── Colors ──────────────────────────────────────────────────
BG_DARK  = "#0D1117"
BG_PANEL = "#161B22"
BG_CARD  = "#21262D"
ACCENT   = "#58A6FF"
GREEN    = "#3FB950"
RED      = "#F85149"
YELLOW   = "#D29922"
TEXT_PRI = "#E6EDF3"
TEXT_SEC = "#8B949E"
BORDER   = "#30363D"
PURPLE   = "#BC8CFF"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ══════════════════════════════════════════════════════════
#  BILLING WINDOW
# ══════════════════════════════════════════════════════════
class BillingWindow(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG_DARK)
        self.app          = app
        self.session_id   = ""
        self.cart_items   = []
        self.total_price  = 0.0
        self.total_weight = 0.0
        self._build_ui()
        self._new_session()

    def _build_ui(self):
        self.pack(fill=tk.BOTH, expand=True)

        # Header
        hdr = tk.Frame(self, bg="#1C2128", pady=10)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="🛒  SELF-CHECKOUT BILLING COUNTER",
                 font=("Courier New", 15, "bold"),
                 bg="#1C2128", fg=ACCENT).pack(side=tk.LEFT, padx=20)
        self.lbl_session = tk.Label(hdr, text="", font=("Courier New", 10),
                                    bg="#1C2128", fg=TEXT_SEC)
        self.lbl_session.pack(side=tk.RIGHT, padx=20)

        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # ── Left side ──────────────────────────────────────
        left = tk.Frame(body, bg=BG_DARK)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scanner card
        sc = tk.LabelFrame(left, text="  📷  BARCODE SCANNER  ",
                           bg=BG_PANEL, fg=ACCENT, bd=1,
                           font=("Courier New", 10, "bold"), relief=tk.SOLID)
        sc.pack(fill=tk.X, padx=5, pady=5)

        row1 = tk.Frame(sc, bg=BG_PANEL, pady=8)
        row1.pack(fill=tk.X, padx=10)
        tk.Label(row1, text="Barcode:", bg=BG_PANEL, fg=TEXT_PRI,
                 font=("Courier New", 10)).pack(side=tk.LEFT)
        self.entry_bc = tk.Entry(row1, font=("Courier New", 13, "bold"),
                                 bg=BG_CARD, fg=ACCENT, insertbackground=ACCENT,
                                 relief=tk.FLAT, width=22, bd=5)
        self.entry_bc.pack(side=tk.LEFT, padx=8)
        self.entry_bc.bind("<Return>", lambda e: self._scan())

        row2 = tk.Frame(sc, bg=BG_PANEL)
        row2.pack(fill=tk.X, padx=10, pady=(0, 8))
        tk.Label(row2, text="Qty:", bg=BG_PANEL, fg=TEXT_PRI,
                 font=("Courier New", 10)).pack(side=tk.LEFT)
        self.spin_qty = tk.Spinbox(row2, from_=1, to=20, width=5,
                                   font=("Courier New", 12),
                                   bg=BG_CARD, fg=TEXT_PRI,
                                   buttonbackground=BG_CARD, relief=tk.FLAT)
        self.spin_qty.pack(side=tk.LEFT, padx=8)
        self._btn(row2, "  ADD ITEM  ", ACCENT, self._scan).pack(side=tk.LEFT, padx=8)

        # Product info
        self.prod_card = tk.Frame(left, bg=BG_CARD, bd=1, relief=tk.SOLID)
        self.prod_card.pack(fill=tk.X, padx=5, pady=3)
        self.lbl_prod = tk.Label(self.prod_card,
                                  text="[ Scan a product to see details ]",
                                  bg=BG_CARD, fg=TEXT_SEC,
                                  font=("Courier New", 9), pady=6)
        self.lbl_prod.pack()

        # Cart table
        ct = tk.LabelFrame(left, text="  🧾  CART  ",
                           bg=BG_PANEL, fg=ACCENT, bd=1,
                           font=("Courier New", 10, "bold"), relief=tk.SOLID)
        ct.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        cols = ("barcode","product","qty","price","weight")
        self.tree = ttk.Treeview(ct, columns=cols, show="headings", height=11)
        hdrs = {"barcode":"Barcode","product":"Product","qty":"Qty",
                "price":"Price(Rs)","weight":"Wt(g)"}
        ws   = {"barcode":130,"product":210,"qty":40,"price":80,"weight":75}
        style = ttk.Style(); style.theme_use("clam")
        style.configure("Treeview", background=BG_CARD,
                        fieldbackground=BG_CARD, foreground=TEXT_PRI,
                        rowheight=26, font=("Courier New", 9))
        style.configure("Treeview.Heading", background=BG_PANEL,
                        foreground=ACCENT, font=("Courier New", 9, "bold"))
        style.map("Treeview", background=[("selected","#264F78")])
        for c in cols:
            self.tree.heading(c, text=hdrs[c])
            self.tree.column(c, width=ws[c], anchor=tk.CENTER)
        vsb = ttk.Scrollbar(ct, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        rm = tk.Frame(left, bg=BG_DARK)
        rm.pack(fill=tk.X, padx=5, pady=3)
        self._btn(rm, "🗑  Remove Selected", RED,    self._remove).pack(side=tk.LEFT)
        self._btn(rm, "🔄  Clear Cart",      YELLOW, self._clear).pack(side=tk.LEFT, padx=8)

        # ── Right summary panel ────────────────────────────
        right = tk.Frame(body, bg=BG_PANEL, width=255, bd=1, relief=tk.SOLID)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(10,5), pady=5)
        right.pack_propagate(False)

        tk.Label(right, text="ORDER SUMMARY", bg=BG_PANEL, fg=ACCENT,
                 font=("Courier New", 11, "bold"), pady=12).pack()
        ttk.Separator(right, orient="horizontal").pack(fill=tk.X, padx=10)

        inf = tk.Frame(right, bg=BG_PANEL, pady=8)
        inf.pack(fill=tk.X, padx=15)
        self.lbl_items  = self._srow(inf, "Items")
        self.lbl_wt     = self._srow(inf, "Total Weight")
        self.lbl_total  = self._srow(inf, "Total Price", big=True, color=GREEN)

        ttk.Separator(right, orient="horizontal").pack(fill=tk.X, padx=10, pady=4)

        wf = tk.Frame(right, bg="#1C2128", bd=1, relief=tk.SOLID, pady=6)
        wf.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(wf, text="⚖  EXPECTED WEIGHT", bg="#1C2128",
                 fg=TEXT_SEC, font=("Courier New", 8)).pack()
        self.lbl_wt_big = tk.Label(wf, text="0 g", bg="#1C2128",
                                    fg=YELLOW, font=("Courier New", 22, "bold"))
        self.lbl_wt_big.pack()

        ba = tk.Frame(right, bg=BG_PANEL, pady=8)
        ba.pack(fill=tk.X, padx=10)
        self._btn(ba, "💳  GENERATE BILL",  GREEN,  self._bill,  big=True).pack(fill=tk.X, pady=4)
        self._btn(ba, "🔁  NEW CUSTOMER",   ACCENT, self._new_session, big=True).pack(fill=tk.X, pady=4)
        self._btn(ba, "🚪  EXIT GATE  →",   YELLOW, self.app.show_exit, big=True).pack(fill=tk.X, pady=4)

        self.status = tk.Label(self, text="Ready — scan a product",
                               bg="#1C2128", fg=TEXT_SEC,
                               font=("Courier New", 9), anchor=tk.W, pady=4)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)
        self.entry_bc.focus()

    def _srow(self, p, label, big=False, color=TEXT_PRI):
        r = tk.Frame(p, bg=BG_PANEL); r.pack(fill=tk.X, pady=2)
        tk.Label(r, text=label+":", bg=BG_PANEL, fg=TEXT_SEC,
                 font=("Courier New", 9)).pack(side=tk.LEFT)
        lbl = tk.Label(r, text="—", bg=BG_PANEL, fg=color,
                       font=("Courier New", 13 if big else 10,
                             "bold" if big else "normal"))
        lbl.pack(side=tk.RIGHT)
        return lbl

    def _btn(self, p, txt, col, cmd, big=False):
        return tk.Button(p, text=txt, bg=col,
                         fg="white" if col != YELLOW else "black",
                         font=("Courier New", 10 if big else 9, "bold"),
                         relief=tk.FLAT, cursor="hand2", command=cmd,
                         activebackground=col,
                         padx=10, pady=6 if big else 3, bd=0)

    def _new_session(self):
        self.session_id = str(uuid.uuid4())[:12].upper()
        self.cart_items = []; self.total_price = 0.0; self.total_weight = 0.0
        for r in self.tree.get_children(): self.tree.delete(r)
        self._upd()
        self.lbl_session.config(text=f"Session: {self.session_id}")
        self._st(f"New session — {self.session_id}", ACCENT)
        self.lbl_prod.config(text="[ Scan a product to see details ]", fg=TEXT_SEC)
        c = get_conn(); cur = c.cursor()
        cur.execute("INSERT OR IGNORE INTO sessions (session_id) VALUES (?)", (self.session_id,))
        c.commit(); c.close()
        self.entry_bc.focus()

    def _scan(self):
        bc  = self.entry_bc.get().strip()
        qty = int(self.spin_qty.get())
        if not bc: return
        conn = get_conn(); cur = conn.cursor()
        cur.execute("SELECT * FROM products WHERE barcode=?", (bc,))
        p = cur.fetchone(); conn.close()
        if not p:
            self._st(f"⚠  Barcode {bc} not found!", RED)
            self.lbl_prod.config(text=f"  ❌  Not found: {bc}", fg=RED, bg=BG_CARD)
            self.entry_bc.delete(0, tk.END); return

        item = {"barcode": p["barcode"], "name": p["name"], "qty": qty,
                "price":  p["price"]*qty, "weight": p["weight_g"]*qty,
                "price_each": p["price"], "weight_g": p["weight_g"]}
        self.cart_items.append(item)
        self.total_price  += item["price"]
        self.total_weight += item["weight"]
        self.tree.insert("", tk.END, values=(
            item["barcode"], item["name"], item["qty"],
            f"Rs.{item['price']:.2f}", f"{item['weight']:.0f}g"))

        conn = get_conn(); cur = conn.cursor()
        cur.execute("""INSERT INTO session_items
                       (session_id,barcode,product_name,qty,price_each,weight_g)
                       VALUES (?,?,?,?,?,?)""",
                    (self.session_id, item["barcode"], item["name"],
                     qty, item["price_each"], item["weight"]))
        cur.execute("""UPDATE sessions SET total_price=?,total_weight_g=?,
                       item_count=item_count+? WHERE session_id=?""",
                    (self.total_price, self.total_weight, qty, self.session_id))
        conn.commit(); conn.close()
        self._upd()
        self.lbl_prod.config(
            text=f"  ✅  {p['name']}  |  {p['brand']}  |  "
                 f"Rs.{p['price']:.2f}  |  {p['weight_g']}g",
            fg=GREEN, bg=BG_CARD)
        self._st(f"✅  Added: {p['name']} ×{qty}", GREEN)
        self.entry_bc.delete(0, tk.END)
        self.spin_qty.delete(0, tk.END); self.spin_qty.insert(0, "1")
        self.entry_bc.focus()

    def _remove(self):
        sel = self.tree.selection()
        if not sel: return
        idx  = self.tree.index(sel[0])
        item = self.cart_items.pop(idx)
        self.total_price  -= item["price"]
        self.total_weight -= item["weight"]
        self.tree.delete(sel[0]); self._upd()

    def _clear(self):
        if not messagebox.askyesno("Clear", "Clear all items?"): return
        self.cart_items = []; self.total_price = 0.0; self.total_weight = 0.0
        for r in self.tree.get_children(): self.tree.delete(r)
        self._upd()

    def _upd(self):
        self.lbl_items.config(text=str(len(self.cart_items)))
        self.lbl_wt.config(text=f"{self.total_weight:.0f} g")
        self.lbl_total.config(text=f"Rs. {self.total_price:.2f}")
        self.lbl_wt_big.config(text=f"{self.total_weight:.0f} g")

    def _bill(self):
        if not self.cart_items:
            messagebox.showwarning("Empty", "No items scanned!"); return
        conn = get_conn(); cur = conn.cursor()
        cur.execute("UPDATE sessions SET status='billed' WHERE session_id=?",
                    (self.session_id,))
        conn.commit(); conn.close()
        path = self._pdf()
        self._st(f"✅  Bill saved: {os.path.basename(path)}", GREEN)
        messagebox.showinfo("Bill Generated",
                            f"Bill saved!\n\nSession ID: {self.session_id}\n"
                            f"Expected Weight: {self.total_weight:.0f} g\n\n"
                            "➡  Proceed to Exit Gate for weight verification.")
        self.app.set_active_session(self.session_id, self.total_weight)

    def _pdf(self):
        fn   = f"Bill_{self.session_id}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        path = os.path.join(BILL_DIR, fn)
        doc  = SimpleDocTemplate(path, pagesize=A4,
                                 topMargin=20*mm, bottomMargin=20*mm)
        st   = getSampleStyleSheet(); story = []
        story.append(Paragraph(STORE_NAME,
                     ParagraphStyle("t", parent=st["Title"], fontSize=18)))
        story.append(Paragraph(STORE_ADDR, st["Normal"]))
        story.append(Paragraph(
            f"Date: {datetime.datetime.now().strftime('%d %b %Y  %H:%M')}", st["Normal"]))
        story.append(Paragraph(
            f"Session ID: <b>{self.session_id}</b>", st["Normal"]))
        story.append(Spacer(1, 8*mm))
        data = [["#","Barcode","Product","Qty","Price(Rs)","Weight(g)"]]
        for i, it in enumerate(self.cart_items, 1):
            data.append([i, it["barcode"], it["name"], it["qty"],
                         f"Rs.{it['price']:.2f}", f"{it['weight']:.0f}"])
        data.append(["","","","TOTAL",
                     f"Rs.{self.total_price:.2f}", f"{self.total_weight:.0f}g"])
        t = Table(data, colWidths=[12*mm,35*mm,65*mm,15*mm,25*mm,25*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1a1a2e")),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
            ("ROWBACKGROUNDS",(0,1),(-1,-2),
             [colors.HexColor("#f9f9f9"),colors.white]),
            ("FONTNAME",(0,-1),(-1,-1),"Helvetica-Bold"),
            ("BACKGROUND",(0,-1),(-1,-1),colors.HexColor("#e8f5e9")),
            ("GRID",(0,0),(-1,-1),0.5,colors.grey),
        ]))
        story.append(t)
        story.append(Spacer(1,6*mm))
        story.append(Paragraph(
            f"EXPECTED BAG WEIGHT AT EXIT GATE: <b>{self.total_weight:.0f} g</b>",
            ParagraphStyle("w", parent=st["Normal"], fontSize=12,
                           textColor=colors.HexColor("#1565C0"))))
        doc.build(story)
        return path

    def _st(self, msg, color=TEXT_PRI):
        self.status.config(text=f"  {msg}", fg=color)


# ══════════════════════════════════════════════════════════
#  EXIT GATE WINDOW  (with AUTO + MANUAL modes)
# ══════════════════════════════════════════════════════════
class ExitGateWindow(tk.Frame):
    def __init__(self, master, app):
        super().__init__(master, bg=BG_DARK)
        self.app              = app
        self.active_sid       = None
        self.expected_weight  = 0.0
        self.mode             = tk.StringVar(value="manual")  # "auto" | "manual"
        self.serial_conn      = None
        self.auto_thread      = None
        self.auto_running     = False
        self.available_ports  = []
        self._build_ui()

    # ── Build UI ───────────────────────────────────────────
    def _build_ui(self):
        self.pack(fill=tk.BOTH, expand=True)

        # Header
        hdr = tk.Frame(self, bg="#1C2128", pady=10)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text="🚪  EXIT GATE — WEIGHT VERIFICATION",
                 font=("Courier New", 15, "bold"),
                 bg="#1C2128", fg=YELLOW).pack(side=tk.LEFT, padx=20)
        self._btn(hdr, "← BILLING", ACCENT, self.app.show_billing).pack(side=tk.RIGHT, padx=20)

        body = tk.Frame(self, bg=BG_DARK)
        body.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        # ── Left side ──────────────────────────────────────
        left = tk.Frame(body, bg=BG_DARK)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Session Lookup
        sl = tk.LabelFrame(left, text="  🔍  SESSION LOOKUP  ",
                           bg=BG_PANEL, fg=YELLOW, bd=1,
                           font=("Courier New", 10, "bold"), relief=tk.SOLID)
        sl.pack(fill=tk.X, pady=5)
        sr = tk.Frame(sl, bg=BG_PANEL, pady=8)
        sr.pack(fill=tk.X, padx=10)
        tk.Label(sr, text="Session ID:", bg=BG_PANEL, fg=TEXT_PRI,
                 font=("Courier New", 10)).pack(side=tk.LEFT)
        self.entry_sid = tk.Entry(sr, font=("Courier New", 12, "bold"),
                                  bg=BG_CARD, fg=YELLOW,
                                  insertbackground=YELLOW,
                                  relief=tk.FLAT, width=16, bd=5)
        self.entry_sid.pack(side=tk.LEFT, padx=8)
        self.entry_sid.bind("<Return>", lambda e: self._load_session())
        self._btn(sr, "LOAD", YELLOW, self._load_session).pack(side=tk.LEFT)

        self.sess_info = tk.Label(sl,
                                   text="[ Load a session to begin ]",
                                   bg=BG_PANEL, fg=TEXT_SEC,
                                   font=("Courier New", 9), pady=6)
        self.sess_info.pack(fill=tk.X, padx=10)

        # ══ MODE TOGGLE ════════════════════════════════════
        mode_card = tk.LabelFrame(left,
                                   text="  ⚙  WEIGHT INPUT MODE  ",
                                   bg=BG_PANEL, fg=PURPLE, bd=1,
                                   font=("Courier New", 10, "bold"),
                                   relief=tk.SOLID)
        mode_card.pack(fill=tk.X, pady=5)

        mode_row = tk.Frame(mode_card, bg=BG_PANEL, pady=8)
        mode_row.pack(fill=tk.X, padx=10)

        # AUTO radio
        self.rb_auto = tk.Radiobutton(
            mode_row, text="🔌  AUTO  (Arduino Load Cell)",
            variable=self.mode, value="auto",
            command=self._on_mode_change,
            bg=BG_PANEL, fg=GREEN,
            selectcolor=BG_CARD,
            activebackground=BG_PANEL,
            font=("Courier New", 10, "bold"),
            cursor="hand2")
        self.rb_auto.pack(side=tk.LEFT, padx=5)

        # MANUAL radio
        self.rb_manual = tk.Radiobutton(
            mode_row, text="✏️  MANUAL  (Type weight)",
            variable=self.mode, value="manual",
            command=self._on_mode_change,
            bg=BG_PANEL, fg=ACCENT,
            selectcolor=BG_CARD,
            activebackground=BG_PANEL,
            font=("Courier New", 10, "bold"),
            cursor="hand2")
        self.rb_manual.pack(side=tk.LEFT, padx=20)

        # ── AUTO sub-panel ─────────────────────────────────
        self.auto_panel = tk.Frame(mode_card, bg=BG_CARD,
                                    bd=1, relief=tk.SOLID)
        self.auto_panel.pack(fill=tk.X, padx=10, pady=(0, 8))

        ap_row1 = tk.Frame(self.auto_panel, bg=BG_CARD, pady=6)
        ap_row1.pack(fill=tk.X, padx=8)
        tk.Label(ap_row1, text="COM Port:", bg=BG_CARD,
                 fg=TEXT_PRI, font=("Courier New", 9)).pack(side=tk.LEFT)
        self.combo_port = ttk.Combobox(ap_row1, width=12,
                                        font=("Courier New", 10),
                                        state="readonly")
        self.combo_port.pack(side=tk.LEFT, padx=6)
        self._btn(ap_row1, "🔄 Refresh", ACCENT,
                  self._refresh_ports, ).pack(side=tk.LEFT, padx=4)
        self._btn(ap_row1, "🔗 Connect", GREEN,
                  self._connect_arduino).pack(side=tk.LEFT, padx=4)
        self._btn(ap_row1, "❌ Disconnect", RED,
                  self._disconnect_arduino).pack(side=tk.LEFT, padx=4)

        ap_row2 = tk.Frame(self.auto_panel, bg=BG_CARD, pady=4)
        ap_row2.pack(fill=tk.X, padx=8)
        tk.Label(ap_row2, text="Status:", bg=BG_CARD,
                 fg=TEXT_SEC, font=("Courier New", 8)).pack(side=tk.LEFT)
        self.lbl_serial_status = tk.Label(
            ap_row2,
            text="⚫  Not Connected",
            bg=BG_CARD, fg=TEXT_SEC,
            font=("Courier New", 9, "bold"))
        self.lbl_serial_status.pack(side=tk.LEFT, padx=6)

        self.lbl_live_weight = tk.Label(
            self.auto_panel,
            text="📡  Waiting for Arduino...",
            bg=BG_CARD, fg=TEXT_SEC,
            font=("Courier New", 11), pady=4)
        self.lbl_live_weight.pack()

        # ── MANUAL sub-panel ───────────────────────────────
        self.manual_panel = tk.Frame(mode_card, bg=BG_CARD,
                                      bd=1, relief=tk.SOLID)
        self.manual_panel.pack(fill=tk.X, padx=10, pady=(0, 8))

        mp_row = tk.Frame(self.manual_panel, bg=BG_CARD, pady=10)
        mp_row.pack(fill=tk.X, padx=10)
        tk.Label(mp_row, text="Enter weight (grams):",
                 bg=BG_CARD, fg=TEXT_PRI,
                 font=("Courier New", 10)).pack(side=tk.LEFT)
        self.entry_wt = tk.Entry(mp_row,
                                  font=("Courier New", 14, "bold"),
                                  bg="#1C2128", fg=ACCENT,
                                  insertbackground=ACCENT,
                                  relief=tk.FLAT, width=12, bd=5)
        self.entry_wt.pack(side=tk.LEFT, padx=8)
        self.entry_wt.bind("<Return>", lambda e: self._verify_manual())

        self._btn(self.manual_panel,
                  "  ✅  VERIFY WEIGHT  ",
                  GREEN, self._verify_manual, big=True).pack(pady=8)

        tk.Label(self.manual_panel,
                 text="(Simulates load cell for demo/testing)",
                 bg=BG_CARD, fg=TEXT_SEC,
                 font=("Courier New", 7), pady=3).pack()

        # Verification Log
        lf = tk.LabelFrame(left, text="  📋  VERIFICATION LOG  ",
                           bg=BG_PANEL, fg=ACCENT, bd=1,
                           font=("Courier New", 10, "bold"), relief=tk.SOLID)
        lf.pack(fill=tk.BOTH, expand=True, pady=5)

        cols = ("time","session","expected","actual","diff","result")
        self.log_tree = ttk.Treeview(lf, columns=cols,
                                      show="headings", height=7)
        hh = {"time":"Time","session":"Session","expected":"Exp(g)",
              "actual":"Act(g)","diff":"Diff(g)","result":"Result"}
        ws = {"time":85,"session":110,"expected":70,
              "actual":70,"diff":65,"result":95}
        for c in cols:
            self.log_tree.heading(c, text=hh[c])
            self.log_tree.column(c, width=ws[c], anchor=tk.CENTER)
        self.log_tree.tag_configure("matched",  background="#0d2818", foreground=GREEN)
        self.log_tree.tag_configure("mismatch", background="#2d0f0f", foreground=RED)
        vsb = ttk.Scrollbar(lf, orient="vertical", command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=vsb.set)
        self.log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        # ── Right hardware panel ────────────────────────────
        right = tk.Frame(body, bg=BG_PANEL, width=290,
                         bd=1, relief=tk.SOLID)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(12,0))
        right.pack_propagate(False)

        tk.Label(right, text="HARDWARE PANEL",
                 bg=BG_PANEL, fg=ACCENT,
                 font=("Courier New", 11, "bold"), pady=12).pack()
        ttk.Separator(right, orient="horizontal").pack(fill=tk.X, padx=10)

        # LCD
        lcd_o = tk.Frame(right, bg="#111", bd=3, relief=tk.SUNKEN, pady=2)
        lcd_o.pack(padx=16, pady=14, fill=tk.X)
        tk.Label(lcd_o, text="[ LCD 16x2 DISPLAY ]", bg="#111",
                 fg="#333", font=("Courier New", 6)).pack()
        self.lcd1 = tk.Label(lcd_o, text="SMARTMART SYSTEM",
                              bg="#1a3a1a", fg="#00FF41",
                              font=("Courier New", 12, "bold"), pady=5)
        self.lcd1.pack(fill=tk.X, padx=4)
        self.lcd2 = tk.Label(lcd_o, text="Place bag on scale",
                              bg="#1a3a1a", fg="#00FF41",
                              font=("Courier New", 11), pady=5)
        self.lcd2.pack(fill=tk.X, padx=4)

        # LEDs
        leds_f = tk.Frame(right, bg=BG_PANEL, pady=6)
        leds_f.pack()
        tk.Label(leds_f, text="LED INDICATORS",
                 bg=BG_PANEL, fg=TEXT_SEC,
                 font=("Courier New", 8)).pack()
        leds_row = tk.Frame(leds_f, bg=BG_PANEL, pady=6)
        leds_row.pack()

        gl = tk.Frame(leds_row, bg=BG_PANEL)
        gl.pack(side=tk.LEFT, padx=18)
        self.cv_green = tk.Canvas(gl, width=48, height=48,
                                   bg=BG_PANEL, highlightthickness=0)
        self.cv_green.pack()
        self._led_off(self.cv_green, "#1a3a1a")
        tk.Label(gl, text="GREEN\n(PASS)", bg=BG_PANEL, fg=TEXT_SEC,
                 font=("Courier New", 7), justify=tk.CENTER).pack()

        rl = tk.Frame(leds_row, bg=BG_PANEL)
        rl.pack(side=tk.LEFT, padx=18)
        self.cv_red = tk.Canvas(rl, width=48, height=48,
                                 bg=BG_PANEL, highlightthickness=0)
        self.cv_red.pack()
        self._led_off(self.cv_red, "#3a1a1a")
        tk.Label(rl, text="RED\n(FAIL)", bg=BG_PANEL, fg=TEXT_SEC,
                 font=("Courier New", 7), justify=tk.CENTER).pack()

        # Buzzer
        tk.Label(right, text="BUZZER", bg=BG_PANEL, fg=TEXT_SEC,
                 font=("Courier New", 8)).pack(pady=(8,0))
        self.buzzer_lbl = tk.Label(right, text="🔇  SILENT",
                                    bg="#1a1a1a", fg=TEXT_SEC,
                                    font=("Courier New", 10, "bold"),
                                    pady=5, relief=tk.SUNKEN)
        self.buzzer_lbl.pack(fill=tk.X, padx=18, pady=4)

        # Weight comparison
        ttk.Separator(right, orient="horizontal").pack(fill=tk.X, padx=10, pady=8)
        tk.Label(right, text="WEIGHT COMPARISON",
                 bg=BG_PANEL, fg=TEXT_SEC,
                 font=("Courier New", 8)).pack()
        self.lbl_exp = tk.Label(right, text="Expected : —",
                                 bg=BG_PANEL, fg=ACCENT,
                                 font=("Courier New", 10))
        self.lbl_exp.pack(pady=2)
        self.lbl_act = tk.Label(right, text="Actual    : —",
                                 bg=BG_PANEL, fg=TEXT_PRI,
                                 font=("Courier New", 10))
        self.lbl_act.pack(pady=2)
        self.lbl_dif = tk.Label(right, text="Difference: —",
                                 bg=BG_PANEL, fg=TEXT_SEC,
                                 font=("Courier New", 10))
        self.lbl_dif.pack(pady=2)
        tk.Label(right, text=f"Tolerance : ±{TOLERANCE}g",
                 bg=BG_PANEL, fg=TEXT_SEC,
                 font=("Courier New", 8)).pack(pady=4)

        # Mode indicator
        ttk.Separator(right, orient="horizontal").pack(fill=tk.X, padx=10, pady=4)
        self.lbl_mode_indicator = tk.Label(
            right, text="MODE: MANUAL",
            bg=BG_PANEL, fg=ACCENT,
            font=("Courier New", 9, "bold"))
        self.lbl_mode_indicator.pack(pady=4)

        # Status bar
        self.status = tk.Label(self, text="Exit Gate Ready",
                               bg="#1C2128", fg=TEXT_SEC,
                               font=("Courier New", 9),
                               anchor=tk.W, pady=4)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

        self._refresh_ports()
        self._load_log()

    # ── Mode Toggle ────────────────────────────────────────
    def _on_mode_change(self):
        m = self.mode.get()
        # Guard: lbl_mode_indicator may not be built yet during __init__
        has_indicator = hasattr(self, "lbl_mode_indicator")
        if m == "auto":
            self.auto_panel.pack(fill=tk.X, padx=10, pady=(0,8))
            self.manual_panel.pack_forget()
            if has_indicator:
                self.lbl_mode_indicator.config(
                    text="MODE: AUTO (Arduino)", fg=GREEN)
            if not SERIAL_AVAILABLE:
                messagebox.showwarning(
                    "PySerial Missing",
                    "pyserial not installed!\n\nRun:\n  pip install pyserial\n\nThen restart the app.")
                self.mode.set("manual")
                self._on_mode_change()
        else:
            self.manual_panel.pack(fill=tk.X, padx=10, pady=(0,8))
            self.auto_panel.pack_forget()
            if has_indicator:
                self.lbl_mode_indicator.config(
                    text="MODE: MANUAL (Demo)", fg=ACCENT)
            self._stop_auto()

    # ── Serial / Arduino ───────────────────────────────────
    def _refresh_ports(self):
        if not SERIAL_AVAILABLE:
            self.combo_port["values"] = ["PySerial not installed"]
            return
        ports = [p.device for p in serial.tools.list_ports.comports()]
        self.available_ports = ports
        self.combo_port["values"] = ports if ports else ["No ports found"]
        if ports:
            self.combo_port.current(0)
        self._st(f"Found {len(ports)} COM port(s)", ACCENT)

    def _connect_arduino(self):
        if not SERIAL_AVAILABLE:
            messagebox.showerror("Error","pip install pyserial first!"); return
        port = self.combo_port.get()
        if not port or "No ports" in port or "not installed" in port:
            messagebox.showwarning("No Port","Select a valid COM port."); return
        try:
            if self.serial_conn and self.serial_conn.is_open:
                self.serial_conn.close()
            self.serial_conn = serial.Serial(port, BAUD_RATE, timeout=2)
            time.sleep(2)   # wait for Arduino reset
            self.lbl_serial_status.config(
                text=f"🟢  Connected: {port}", fg=GREEN)
            self._st(f"✅  Arduino connected on {port}", GREEN)
            self.lcd1.config(text="Arduino Connected", bg="#1a3a1a")
            self.lcd2.config(text=f"Port: {port}", bg="#1a3a1a")
            # Start auto-read thread
            self._start_auto_read()
        except Exception as e:
            messagebox.showerror("Connection Failed", str(e))
            self.lbl_serial_status.config(
                text=f"🔴  Failed: {e}", fg=RED)

    def _disconnect_arduino(self):
        self._stop_auto()
        if self.serial_conn:
            try: self.serial_conn.close()
            except: pass
            self.serial_conn = None
        self.lbl_serial_status.config(
            text="⚫  Disconnected", fg=TEXT_SEC)
        self.lbl_live_weight.config(
            text="📡  Waiting for Arduino...", fg=TEXT_SEC)
        self._st("Arduino disconnected.", TEXT_SEC)

    def _start_auto_read(self):
        self._stop_auto()
        self.auto_running = True
        self.auto_thread  = threading.Thread(
            target=self._auto_read_loop, daemon=True)
        self.auto_thread.start()

    def _stop_auto(self):
        self.auto_running = False

    def _auto_read_loop(self):
        """
        Runs in background thread.
        Sends TARE to Arduino, then listens for weight data.
        When Arduino sends WEIGHT:<value>, triggers verification.
        """
        if not self.serial_conn: return
        try:
            # Send TARE first
            self.serial_conn.write(b"TARE\n")
            time.sleep(1)
        except: pass

        buffer = ""
        while self.auto_running and self.serial_conn:
            try:
                if self.serial_conn.in_waiting > 0:
                    ch = self.serial_conn.read().decode("utf-8", errors="ignore")
                    if ch == "\n":
                        line = buffer.strip()
                        buffer = ""
                        self._handle_serial_line(line)
                    else:
                        buffer += ch
                else:
                    time.sleep(0.05)
            except Exception as e:
                self.after(0, lambda: self.lbl_serial_status.config(
                    text=f"🔴  Error: {e}", fg=RED))
                break

    def _handle_serial_line(self, line):
        """Parse messages from Arduino"""
        if not line: return

        # Live weight update: WEIGHT:523.5
        if line.startswith("WEIGHT:"):
            val = line.split(":")[1].strip()
            try:
                w = float(val)
                self.after(0, lambda: self.lbl_live_weight.config(
                    text=f"📡  Live: {w:.0f} g",
                    fg=YELLOW,
                    font=("Courier New", 13, "bold")))
                self.after(0, lambda: self.lcd2.config(
                    text=f"Weight: {w:.0f}g"))
            except: pass

        # Result from Arduino: RESULT:MATCHED:520.3 or RESULT:MISMATCH:610.2:90.0
        elif line.startswith("RESULT:"):
            parts = line.split(":")
            result  = parts[1]
            actual  = float(parts[2]) if len(parts) > 2 else 0.0
            self.after(0, lambda: self._process_result(actual))

        # Arduino ready
        elif line in ("READY", "RESET:READY"):
            self.after(0, lambda: self.lbl_serial_status.config(
                text="🟢  Arduino Ready", fg=GREEN))

        # Tared
        elif line == "ACK:TARED":
            self.after(0, lambda: self._st("Load cell zeroed (tared)", GREEN))

    def _send_verify_command(self):
        """Tell Arduino to read weight and compare"""
        if self.serial_conn and self.serial_conn.is_open:
            cmd = f"VERIFY:{self.expected_weight:.0f}\n"
            self.serial_conn.write(cmd.encode())
            self._st(f"📡  Sent VERIFY:{self.expected_weight:.0f}g to Arduino", ACCENT)
            self.lcd1.config(text="Verifying...", bg="#1a3a1a")
            self.lcd2.config(text=f"Exp:{self.expected_weight:.0f}g Place bag")

    # ── Session Load ───────────────────────────────────────
    def activate(self, sid=None, weight=None):
        if sid:
            self.active_sid      = sid
            self.expected_weight = weight or 0.0
            self.entry_sid.delete(0, tk.END)
            self.entry_sid.insert(0, sid)
            self._load_session()

    def _load_session(self):
        sid = self.entry_sid.get().strip().upper()
        if not sid: return
        conn = get_conn(); cur = conn.cursor()
        cur.execute("SELECT * FROM sessions WHERE session_id=?", (sid,))
        s = cur.fetchone(); conn.close()
        if not s:
            self.sess_info.config(
                text=f"  ❌  Session '{sid}' not found!", fg=RED); return

        self.active_sid      = sid
        self.expected_weight = s["total_weight_g"]
        self.sess_info.config(
            text=f"  ✅  {sid}  |  Items:{s['item_count']}  |  "
                 f"Rs.{s['total_price']:.2f}  |  "
                 f"Expected: {s['total_weight_g']:.0f}g  |  {s['status'].upper()}",
            fg=GREEN)
        self.lbl_exp.config(text=f"Expected : {self.expected_weight:.0f} g")
        self.lcd1.config(text=f"Sess:{sid[:10]}")
        self.lcd2.config(text=f"Exp:{self.expected_weight:.0f}g Place bag")
        self._st(f"Session loaded: {sid}", ACCENT)

        # If in AUTO mode, send command to Arduino
        if self.mode.get() == "auto" and self.serial_conn:
            self.after(500, self._send_verify_command)
        else:
            self.entry_wt.focus()

    # ── Manual Verify ──────────────────────────────────────
    def _verify_manual(self):
        if not self.active_sid:
            messagebox.showwarning("No Session","Load a session first!"); return
        try:
            actual = float(self.entry_wt.get().strip())
        except ValueError:
            messagebox.showerror("Invalid","Enter a valid weight in grams."); return
        self._process_result(actual)
        self.entry_wt.delete(0, tk.END)

    # ── Core Verification ──────────────────────────────────
    def _process_result(self, actual):
        if not self.active_sid: return
        expected = self.expected_weight
        diff     = actual - expected
        matched  = abs(diff) <= TOLERANCE

        # Save to DB
        result_str = "MATCHED" if matched else "MISMATCH"
        conn = get_conn(); cur = conn.cursor()
        cur.execute("""INSERT INTO verification_logs
                       (session_id,expected_weight,actual_weight,
                        difference_g,result)
                       VALUES (?,?,?,?,?)""",
                    (self.active_sid, expected, actual, diff, result_str))
        cur.execute("UPDATE sessions SET status=? WHERE session_id=?",
                    ("verified" if matched else "flagged", self.active_sid))
        conn.commit(); conn.close()

        # Update weight display
        self.lbl_act.config(text=f"Actual    : {actual:.0f} g")
        self.lbl_dif.config(text=f"Difference: {diff:+.0f} g",
                             fg=GREEN if matched else RED)

        if matched:
            self._show_pass(actual, expected, diff)
        else:
            self._show_fail(actual, expected, diff)

        self._load_log()

    def _show_pass(self, actual, expected, diff):
        self.lcd1.config(text="  WEIGHT MATCHED!", bg="#0a2a0a", fg="#00FF41")
        self.lcd2.config(text=f"A:{actual:.0f}g E:{expected:.0f}g",
                          bg="#0a2a0a", fg="#00FF41")
        self._led_on(self.cv_green,  "#00FF41")
        self._led_off(self.cv_red,   "#3a1a1a")
        self.buzzer_lbl.config(text="🔇  SILENT", bg="#1a1a1a", fg=TEXT_SEC)
        self._st("✅  MATCHED — Customer may proceed!", GREEN)
        messagebox.showinfo("✅  PASS",
                            f"Weight MATCHED!\n\n"
                            f"Expected : {expected:.0f} g\n"
                            f"Actual   : {actual:.0f} g\n"
                            f"Diff     : {abs(diff):.0f} g\n\n"
                            "🟢 GREEN LED ON\n✅ Customer may proceed!")
        self.after(4000, self._reset_display)

    def _show_fail(self, actual, expected, diff):
        self.lcd1.config(text="  WEIGHT MISMATCH!", bg="#2a0a0a", fg="#FF3333")
        self.lcd2.config(text=f"A:{actual:.0f}g E:{expected:.0f}g ALERT",
                          bg="#2a0a0a", fg="#FF3333")
        self._led_on(self.cv_red,    "#FF3333")
        self._led_off(self.cv_green, "#1a3a1a")
        self.buzzer_lbl.config(text="🔊  BUZZER ON!", bg=RED, fg="white")
        self._st("⚠  MISMATCH — Alert Security!", RED)
        self._flash_buzzer()
        messagebox.showwarning("⚠  MISMATCH — ALERT!",
                               f"Weight MISMATCH!\n\n"
                               f"Expected : {expected:.0f} g\n"
                               f"Actual   : {actual:.0f} g\n"
                               f"Diff     : {diff:+.0f} g\n\n"
                               "🔴 RED LED ON\n🔊 BUZZER ACTIVATED\n"
                               "⚠  Call security!")
        self.after(5000, self._reset_display)

    def _flash_buzzer(self, n=6):
        if n <= 0:
            self.buzzer_lbl.config(text="🔇  SILENT",
                                    bg="#1a1a1a", fg=TEXT_SEC); return
        c = RED if n % 2 == 0 else "#1a1a1a"
        self.buzzer_lbl.config(bg=c)
        self.after(300, lambda: self._flash_buzzer(n-1))

    def _reset_display(self):
        self.lcd1.config(text="SMARTMART SYSTEM",  bg="#1a3a1a", fg="#00FF41")
        self.lcd2.config(text="Place bag on scale", bg="#1a3a1a", fg="#00FF41")
        self._led_off(self.cv_green, "#1a3a1a")
        self._led_off(self.cv_red,   "#3a1a1a")
        self.active_sid      = None
        self.expected_weight = 0.0
        self.lbl_exp.config(text="Expected : —")
        self.lbl_act.config(text="Actual    : —")
        self.lbl_dif.config(text="Difference: —")
        self.entry_sid.delete(0, tk.END)
        self.sess_info.config(
            text="[ Load a session to begin ]", fg=TEXT_SEC)

    # ── LED helpers ────────────────────────────────────────
    def _led_on(self, cv, color):
        cv.delete("all")
        cv.create_oval(3,3,45,45, fill=color, outline="white", width=2)

    def _led_off(self, cv, dim):
        cv.delete("all")
        cv.create_oval(5,5,43,43, fill=dim, outline="#555", width=1)

    def _load_log(self):
        for r in self.log_tree.get_children(): self.log_tree.delete(r)
        conn = get_conn(); cur = conn.cursor()
        cur.execute("""SELECT verified_at,session_id,expected_weight,
                              actual_weight,difference_g,result
                       FROM verification_logs
                       ORDER BY verified_at DESC LIMIT 50""")
        for row in cur.fetchall():
            tag  = "matched" if row["result"]=="MATCHED" else "mismatch"
            icon = "✅" if tag=="matched" else "❌"
            self.log_tree.insert("", tk.END, values=(
                row["verified_at"][11:19],
                row["session_id"],
                f"{row['expected_weight']:.0f}",
                f"{row['actual_weight']:.0f}",
                f"{row['difference_g']:+.0f}",
                f"{icon} {row['result']}"
            ), tags=(tag,))
        conn.close()

    def _btn(self, p, txt, col, cmd, big=False):
        return tk.Button(p, text=txt, bg=col,
                         fg="white" if col!=YELLOW else "black",
                         font=("Courier New", 10 if big else 9, "bold"),
                         relief=tk.FLAT, cursor="hand2",
                         command=cmd, activebackground=col,
                         padx=10, pady=6 if big else 3, bd=0)

    def _st(self, msg, color=TEXT_PRI):
        self.status.config(text=f"  {msg}", fg=color)


# ══════════════════════════════════════════════════════════
#  MAIN APP SHELL
# ══════════════════════════════════════════════════════════
class AntiTheftApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Anti-Theft Weight Verification System — SmartMart")
        self.geometry("1230x800")
        self.minsize(1050, 700)
        self.configure(bg=BG_DARK)

        # Top bar
        nav = tk.Frame(self, bg="#010409", height=44)
        nav.pack(fill=tk.X, side=tk.TOP)
        nav.pack_propagate(False)
        tk.Label(nav, text="⚖  Anti-Theft Weight Verification System",
                 bg="#010409", fg=ACCENT,
                 font=("Courier New", 13, "bold")).pack(side=tk.LEFT, padx=20, pady=10)
        tk.Label(nav, text="SmartMart Superstore  |  Hyderabad",
                 bg="#010409", fg=TEXT_SEC,
                 font=("Courier New", 9)).pack(side=tk.RIGHT, padx=20)

        # Tab bar
        tab = tk.Frame(self, bg="#161B22", height=38)
        tab.pack(fill=tk.X)
        self.btn_bill = tk.Button(tab, text="  🛒  BILLING COUNTER  ",
                                   bg=ACCENT, fg="white",
                                   font=("Courier New", 10, "bold"),
                                   relief=tk.FLAT, cursor="hand2",
                                   command=self.show_billing,
                                   padx=10, pady=8, bd=0)
        self.btn_bill.pack(side=tk.LEFT)
        self.btn_exit = tk.Button(tab, text="  🚪  EXIT GATE  ",
                                   bg=BG_PANEL, fg=TEXT_SEC,
                                   font=("Courier New", 10, "bold"),
                                   relief=tk.FLAT, cursor="hand2",
                                   command=self.show_exit,
                                   padx=10, pady=8, bd=0)
        self.btn_exit.pack(side=tk.LEFT)

        # Container
        self.container = tk.Frame(self, bg=BG_DARK)
        self.container.pack(fill=tk.BOTH, expand=True)

        self.billing_win = BillingWindow(self.container, self)
        self.exit_win    = ExitGateWindow(self.container, self)
        self.exit_win.pack_forget()

        self._pending_sid    = None
        self._pending_weight = None

        # Close handler — cleanly disconnect serial
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def show_billing(self):
        self.exit_win.pack_forget()
        self.billing_win.pack(fill=tk.BOTH, expand=True)
        self.btn_bill.config(bg=ACCENT,   fg="white")
        self.btn_exit.config(bg=BG_PANEL, fg=TEXT_SEC)

    def show_exit(self):
        self.billing_win.pack_forget()
        self.exit_win.pack(fill=tk.BOTH, expand=True)
        self.btn_exit.config(bg=YELLOW, fg="black")
        self.btn_bill.config(bg=BG_PANEL, fg=TEXT_SEC)
        if self._pending_sid:
            self.exit_win.activate(self._pending_sid, self._pending_weight)
            self._pending_sid    = None
            self._pending_weight = None

    def set_active_session(self, sid, weight):
        self._pending_sid    = sid
        self._pending_weight = weight

    def _on_close(self):
        self.exit_win._disconnect_arduino()
        self.destroy()


# ══════════════════════════════════════════════════════════
if __name__ == "__main__":
    from database_setup import init_database
    init_database()
    app = AntiTheftApp()
    app.mainloop()

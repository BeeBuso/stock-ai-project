"""
database.py
ระบบ 'ความจำ' ของโปรเจกต์ — เก็บราคาหุ้นและผลวิเคราะห์ลง SQLite (ไฟล์เดียว ไม่ต้องติดตั้งเซิร์ฟเวอร์)
ทุกครั้งที่รันโปรแกรม ข้อมูลจะถูกเพิ่มต่อจากของเดิม ไม่หายไปไหน
"""

import sqlite3
from datetime import datetime

DB_PATH = "stock_data.db"


def init_db():
    """สร้างตารางถ้ายังไม่มี (เรียกได้ซ้ำๆ อย่างปลอดภัย)"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            close_price REAL,
            change_pct REAL,
            volume INTEGER,
            fetched_at TEXT,
            UNIQUE(ticker, date)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS analysis_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            summary TEXT,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS fear_greed_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            value REAL,
            rating TEXT,
            fetched_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS paper_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            trade_date TEXT NOT NULL,
            entry_price REAL,
            entry_time TEXT,
            tp1 REAL, tp2 REAL, tp3 REAL,
            sl1 REAL, sl2 REAL, sl3 REAL,
            status TEXT DEFAULT 'OPEN',
            exit_price REAL,
            exit_time TEXT,
            pnl_pct REAL,
            score REAL
        )
    """)

    conn.commit()
    conn.close()


def save_price(ticker, date, close_price, change_pct, volume):
    """บันทึก/อัปเดตราคาหุ้น 1 ตัวสำหรับวันที่ระบุ"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO stock_prices
            (ticker, date, close_price, change_pct, volume, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (ticker, date, close_price, change_pct, volume, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_recent_prices(ticker, days=5):
    """ดึงราคาย้อนหลังของหุ้น 1 ตัว ใช้ดูแนวโน้ม"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT date, close_price, change_pct FROM stock_prices
        WHERE ticker = ? ORDER BY date DESC LIMIT ?
    """, (ticker, days))
    rows = cur.fetchall()
    conn.close()
    return rows


def save_analysis(date, summary):
    """บันทึกผลวิเคราะห์ของวันนั้นๆ ไว้เป็นประวัติ"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO analysis_log (date, summary, created_at)
        VALUES (?, ?, ?)
    """, (date, summary, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_past_analysis(limit=3):
    """ดึงผลวิเคราะห์ล่าสุด N ครั้ง เอาไปให้ Claude ใช้เป็น context (นี่คือส่วนที่ทำให้ระบบ 'ไม่ลืมข้อมูลเดิม')"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT date, summary FROM analysis_log ORDER BY date DESC LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


def save_fear_greed(date, value, rating):
    """บันทึกค่า Fear & Greed Index ของวันนั้นๆ ไว้เป็นประวัติ (ใช้ดูแนวโน้มย้อนหลังได้)"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO fear_greed_log (date, value, rating, fetched_at)
        VALUES (?, ?, ?, ?)
    """, (date, value, rating, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_previous_fear_greed():
    """ดึงค่า Fear & Greed Index ครั้งก่อนหน้า (ไม่รวมของวันนี้) เอาไว้เทียบว่าดัชนีขยับไปทางไหน"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT date, value, rating FROM fear_greed_log ORDER BY id DESC LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()
    return row


def open_paper_trade(ticker, trade_date, entry_price, tp1, tp2, tp3, sl1, sl2, sl3, score):
    """บันทึกออเดอร์จำลองที่เพิ่งเปิด (สถานะเริ่มต้น = OPEN)"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO paper_trades
            (ticker, trade_date, entry_price, entry_time, tp1, tp2, tp3, sl1, sl2, sl3, status, score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
    """, (ticker, trade_date, entry_price, datetime.now().isoformat(), tp1, tp2, tp3, sl1, sl2, sl3, score))
    conn.commit()
    trade_id = cur.lastrowid
    conn.close()
    return trade_id


def close_paper_trade(trade_id, exit_price, status, pnl_pct):
    """ปิดออเดอร์จำลอง (status = CLOSED_TP / CLOSED_SL / CLOSED_EOD)"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        UPDATE paper_trades
        SET status = ?, exit_price = ?, exit_time = ?, pnl_pct = ?
        WHERE id = ?
    """, (status, exit_price, datetime.now().isoformat(), pnl_pct, trade_id))
    conn.commit()
    conn.close()


def get_open_trades():
    """ดึงออเดอร์ทั้งหมดที่ยังเปิดอยู่ (ยังไม่ชน TP/SL/หมดวัน)"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM paper_trades WHERE status = 'OPEN'")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_trades_by_date(trade_date):
    """ดึงออเดอร์ทั้งหมด (เปิด+ปิดแล้ว) ของวันที่ระบุ ใช้ทำรายงานสรุปประจำวัน"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM paper_trades WHERE trade_date = ? ORDER BY id", (trade_date,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_closed_trades_since(cutoff_date):
    """ดึงออเดอร์ที่ปิดแล้วทั้งหมด ตั้งแต่วันที่ cutoff_date (YYYY-MM-DD) เป็นต้นมา — ใช้ทำรายงานรายสัปดาห์/รายเดือน"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM paper_trades
        WHERE status != 'OPEN' AND trade_date >= ?
        ORDER BY trade_date
    """, (cutoff_date,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_all_closed_trades():
    """ดึงออเดอร์ที่ปิดแล้วทั้งหมดตั้งแต่เริ่มใช้งานระบบ — ใช้ทำอันดับ Top 10"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM paper_trades WHERE status != 'OPEN' ORDER BY trade_date")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

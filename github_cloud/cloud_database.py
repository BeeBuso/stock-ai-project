"""
cloud_database.py
ฐานข้อมูลเฉพาะฝั่ง GitHub Actions — ใช้ชื่อไฟล์ 'cloud_stock_data.db'
ต่างจาก 'stock_data.db' ที่ใช้บนพีซี เพื่อไม่ให้ชนกันเวลา git pull มาเปิดดูโค้ด
มีแค่ตาราง paper_trades เท่านั้น เพราะระบบจำลอง Day Trade บน cloud ไม่ได้ใช้ Gemini/Fear&Greed
"""

import sqlite3
from datetime import datetime

DB_PATH = "cloud_stock_data.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
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


def open_paper_trade(ticker, trade_date, entry_price, tp1, tp2, tp3, sl1, sl2, sl3, score):
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
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM paper_trades WHERE status = 'OPEN'")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_trades_by_date(trade_date):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM paper_trades WHERE trade_date = ? ORDER BY id", (trade_date,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

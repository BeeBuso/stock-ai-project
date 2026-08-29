"""
test_trading_report.py
สคริปต์ทดสอบ — ส่งรายงานตาราง Day Trade เข้า Discord ด้วย "ข้อมูลตัวอย่าง" (mock data)
ใช้ดูหน้าตารายงานได้ทันที โดยไม่ต้องรอตลาดอเมริกาเปิด (เช่น ทดสอบวันเสาร์-อาทิตย์)

⚠️ ตัวเลขในไฟล์นี้เป็นข้อมูลสมมุติล้วนๆ ไม่ใช่ราคาหุ้นจริง ใช้เพื่อทดสอบรูปแบบการแสดงผลเท่านั้น

วิธีรัน:  python test_trading_report.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

from notify_discord import send_trading_report

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# ออเดอร์จำลองที่ "ยังเปิดอยู่" (ข้อมูลสมมุติ)
mock_open_trades = [
    {"ticker": "NVDA", "entry_price": 185.40, "exit_price": 188.10, "pnl_pct": 1.46, "status": "OPEN"},
    {"ticker": "AMD", "entry_price": 172.20, "exit_price": 170.85, "pnl_pct": -0.78, "status": "OPEN"},
]

# ออเดอร์จำลองที่ "ปิดแล้ววันนี้" (ข้อมูลสมมุติ)
mock_closed_trades = [
    {"ticker": "AAPL", "entry_price": 255.10, "exit_price": 259.80, "pnl_pct": 1.84, "status": "CLOSED_TP"},
    {"ticker": "TSLA", "entry_price": 410.00, "exit_price": 401.20, "pnl_pct": -2.15, "status": "CLOSED_SL"},
    {"ticker": "META", "entry_price": 690.50, "exit_price": 693.10, "pnl_pct": 0.38, "status": "CLOSED_EOD"},
]


def main():
    if not DISCORD_WEBHOOK_URL:
        print("❌ ไม่พบ DISCORD_WEBHOOK_URL ใน .env กรุณาตั้งค่าก่อนรัน")
        return

    print("กำลังส่งรายงานตัวอย่าง (mock data) เข้า Discord ...")
    send_trading_report(DISCORD_WEBHOOK_URL, mock_open_trades, mock_closed_trades)
    print("เสร็จแล้ว เช็คในช่อง Discord ได้เลยครับ")


if __name__ == "__main__":
    main()

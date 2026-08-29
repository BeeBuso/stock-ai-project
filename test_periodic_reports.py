"""
test_periodic_reports.py
ทดสอบรูปแบบรายงานรายสัปดาห์ / รายเดือน / Top 10 ด้วยข้อมูลตัวอย่าง (mock data)
ใช้ดูหน้าตาได้ทันที โดยไม่ต้องรอให้มีออเดอร์จริงสะสมในระบบก่อน

⚠️ ตัวเลขทั้งหมดในไฟล์นี้เป็นข้อมูลสมมุติ ไม่ใช่ผลจริงจากระบบ

วิธีรัน:  python test_periodic_reports.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

from notify_discord import send_trading_report, send_period_summary_report, send_top10_report

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# ออเดอร์จำลองที่ "ยังเปิดอยู่" (ข้อมูลสมมุติ) — ใช้ทดสอบรายงานรายวัน
mock_open_trades = [
    {"ticker": "NVDA", "entry_price": 185.40, "exit_price": 188.10, "pnl_pct": 1.46, "status": "OPEN"},
    {"ticker": "AMD", "entry_price": 172.20, "exit_price": 170.85, "pnl_pct": -0.78, "status": "OPEN"},
]

mock_weekly_stats = {"total": 18, "wins": 9, "losses": 6, "eod": 3, "total_pnl": 12.4, "avg_pnl": 0.69, "win_rate": 60.0}
mock_monthly_stats = {"total": 74, "wins": 34, "losses": 28, "eod": 12, "total_pnl": 21.8, "avg_pnl": 0.29, "win_rate": 54.8}

# รายการเทรดตัวอย่าง (จำลอง) ใช้ทดสอบตารางรายการเทรดในรายงานสัปดาห์/เดือน
mock_trades = [
    {"ticker": "AAPL", "entry_price": 255.10, "exit_price": 259.80, "pnl_pct": 1.84, "status": "CLOSED_TP"},
    {"ticker": "TSLA", "entry_price": 410.00, "exit_price": 401.20, "pnl_pct": -2.15, "status": "CLOSED_SL"},
    {"ticker": "META", "entry_price": 690.50, "exit_price": 693.10, "pnl_pct": 0.38, "status": "CLOSED_EOD"},
    {"ticker": "NVDA", "entry_price": 178.20, "exit_price": 183.40, "pnl_pct": 2.92, "status": "CLOSED_TP"},
    {"ticker": "AMD", "entry_price": 165.00, "exit_price": 161.30, "pnl_pct": -2.24, "status": "CLOSED_SL"},
]

mock_top10 = [
    {"ticker": "NVDA", "total_pnl": 14.2, "count": 8, "win_rate": 75.0},
    {"ticker": "AAPL", "total_pnl": 9.8, "count": 6, "win_rate": 66.7},
    {"ticker": "META", "total_pnl": 7.1, "count": 5, "win_rate": 60.0},
    {"ticker": "AMD", "total_pnl": 5.5, "count": 4, "win_rate": 50.0},
    {"ticker": "MSFT", "total_pnl": 3.2, "count": 4, "win_rate": 50.0},
    {"ticker": "GOOGL", "total_pnl": 1.9, "count": 3, "win_rate": 33.3},
    {"ticker": "JPM", "total_pnl": 0.4, "count": 3, "win_rate": 33.3},
    {"ticker": "DIS", "total_pnl": -1.2, "count": 2, "win_rate": 0.0},
    {"ticker": "TSLA", "total_pnl": -3.8, "count": 3, "win_rate": 33.3},
    {"ticker": "INTC", "total_pnl": -5.1, "count": 2, "win_rate": 0.0},
]


def main():
    if not DISCORD_WEBHOOK_URL:
        print("❌ ไม่พบ DISCORD_WEBHOOK_URL ใน .env กรุณาตั้งค่าก่อนรัน")
        return

    print("กำลังส่งรายงานตัวอย่าง (mock data) ทั้ง 4 ชุดเข้า Discord ...")
    send_trading_report(DISCORD_WEBHOOK_URL, mock_open_trades, mock_trades)
    send_period_summary_report(DISCORD_WEBHOOK_URL, mock_weekly_stats, mock_trades, "📅 สรุปผลรายสัปดาห์ (7 วันล่าสุด)", color=5793266)
    send_period_summary_report(DISCORD_WEBHOOK_URL, mock_monthly_stats, mock_trades, "🗓️ สรุปผลรายเดือน (30 วันล่าสุด)", color=10181046)
    send_top10_report(DISCORD_WEBHOOK_URL, mock_top10)
    print("เสร็จแล้ว เช็คในช่อง Discord ได้เลยครับ (ควรเห็น 4 การ์ดแยกกัน: รายวัน, สัปดาห์, เดือน, Top10)")


if __name__ == "__main__":
    main()

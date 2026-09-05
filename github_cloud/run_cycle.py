"""
run_cycle.py
ไฟล์หลักสำหรับ GitHub Actions โดยเฉพาะ — ทำงาน "1 รอบ" แล้วจบตัวเอง (ไม่มี while loop / time.sleep)
GitHub Actions จะเป็นคนสั่งให้ไฟล์นี้รันซ้ำทุก 15 นาทีเองผ่านตารางเวลา (cron) ที่ตั้งไว้ใน workflow

ทดสอบรันเองบนพีซีได้เหมือนกัน:  python run_cycle.py
(ถ้าทดสอบตอนตลาดปิด จะขึ้นข้อความ 'ตลาดปิดอยู่' แล้วจบโปรแกรมเฉยๆ ไม่ error)
"""

import os
from dotenv import load_dotenv

load_dotenv()

from cloud_database import init_db, get_trades_by_date
from cloud_day_trade_engine import (
    is_market_open, is_near_market_close, today_ny_str,
    scan_and_open_new_trades, check_and_close_trades, force_close_all_eod,
)
from notify_discord import send_trading_report

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def main():
    init_db()
    print(f"===== รอบใหม่ (GitHub Actions) — {today_ny_str()} เวลานิวยอร์ก =====")

    if not is_market_open():
        print("💤 ตลาดปิดอยู่ตอนนี้ (นอกเวลา 9:30-16:00 นิวยอร์ก หรือเสาร์-อาทิตย์) ข้ามรอบนี้")
        return

    if is_near_market_close(minutes_before=10):
        print("⏰ ใกล้ตลาดปิดแล้ว บังคับปิดออเดอร์ที่เหลือทั้งหมด (กติกา Day Trade ห้ามถือข้ามวัน)")
        force_close_all_eod()
        open_trades_display = []
    else:
        print("🔍 กำลังเช็กออเดอร์เก่า ...")
        trade_updates = check_and_close_trades()

        print("🔎 กำลังสแกนหาสัญญาณใหม่ ...")
        scan_and_open_new_trades()

        open_trades_display = [t for t in trade_updates if t["status"] == "OPEN"]

    if DISCORD_WEBHOOK_URL:
        closed_today = [t for t in get_trades_by_date(today_ny_str()) if t["status"] != "OPEN"]
        send_trading_report(DISCORD_WEBHOOK_URL, open_trades_display, closed_today)
    else:
        print("⚠️  ไม่ได้ตั้งค่า DISCORD_WEBHOOK_URL — ข้ามการส่งรายงาน")

    print("===== จบรอบนี้ =====")


if __name__ == "__main__":
    main()

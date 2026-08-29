"""
run_paper_trading.py
ไฟล์หลักของระบบจำลอง Day Trade — รันค้างไว้ตลอดเวลาเพื่อ:
1. เช็กทุก 15 นาทีว่าตลาดอเมริกาเปิดอยู่ไหม (ข้ามรอบถ้าปิด)
2. ถ้าใกล้ตลาดปิด (10 นาทีสุดท้าย) -> บังคับปิดออเดอร์ที่เหลือทั้งหมด (กติกา Day Trade)
3. ไม่งั้น -> เช็กออเดอร์เก่าว่าชน TP/SL หรือยัง + สแกนหาสัญญาณใหม่มาเปิดออเดอร์เพิ่ม
4. ส่งรายงานตารางเข้า Discord ทุกรอบ

⚠️ นี่คือการจำลองเท่านั้น (Paper Trading) ไม่มีการส่งคำสั่งซื้อขายจริงไปยังโบรกเกอร์ใดๆ
   ผลลัพธ์เป็นเพียงเครื่องมือช่วยทดสอบแนวคิดกลยุทธ์ ไม่ใช่คำแนะนำการลงทุน

วิธีรัน:  python run_paper_trading.py
หยุดรัน:  Ctrl+C
"""

import os
import time
from dotenv import load_dotenv

load_dotenv()

from database import init_db, get_open_trades, get_trades_by_date
from day_trade_engine import (
    is_market_open, is_near_market_close, today_ny_str,
    scan_and_open_new_trades, check_and_close_trades, force_close_all_eod,
)
from notify_discord import send_trading_report

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
SCAN_INTERVAL_SECONDS = 15 * 60  # ทุก 15 นาที ตามที่เลือกไว้


def run_cycle():
    print(f"\n{'=' * 50}")
    print(f"รอบใหม่ — {today_ny_str()} (เวลานิวยอร์ก)")

    if not is_market_open():
        print("💤 ตลาดปิดอยู่ตอนนี้ (นอกเวลา 9:30-16:00 เวลานิวยอร์ก หรือเสาร์-อาทิตย์) ข้ามรอบนี้")
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
        print("⚠️  ไม่ได้ตั้งค่า DISCORD_WEBHOOK_URL ใน .env — ข้ามการส่งรายงาน")


def main():
    init_db()
    print("🧪 เริ่มระบบ Day Trade Simulator (Paper Trading)")
    print("⚠️  นี่คือการจำลองเท่านั้น ไม่มีการซื้อขายเงินจริง")
    print(f"   สแกนทุก {SCAN_INTERVAL_SECONDS // 60} นาที | กด Ctrl+C เพื่อหยุด\n")

    while True:
        try:
            run_cycle()
        except Exception as e:
            print(f"❌ เกิดข้อผิดพลาดระหว่างรอบ: {type(e).__name__}: {e}")

        time.sleep(SCAN_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()

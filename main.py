"""
main.py
ไฟล์หลัก — รันไฟล์นี้ไฟล์เดียวเพื่อทำงานครบวงจร:
ดึงข้อมูลหุ้น -> บันทึกความจำ -> วิเคราะห์ด้วย Gemini -> ส่งเข้า Discord
พร้อมแสดง % ความคืบหน้าระหว่างทำงาน

วิธีรัน:  python main.py
"""

import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # ต้องโหลด .env ก่อน import ไฟล์อื่น ไม่งั้นค่า API key จะยังว่างอยู่

from database import init_db, save_analysis
from fetch_data import fetch_all_stocks
from fetch_fear_greed import get_fear_greed
from analyze import analyze_stocks
from notify_discord import send_to_discord

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def print_progress(step_name, pct):
    print(f"[{pct:>3}%] {step_name}")


def main():
    print("=" * 50)
    print(f"เริ่มทำงาน Stock AI — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    print_progress("เตรียมฐานข้อมูล", 5)
    init_db()

    print_progress("เริ่มดึงข้อมูลหุ้น", 10)

    def on_fetch_progress(i, total, ticker):
        pct = 10 + int((i / total) * 40)  # ขั้นดึงข้อมูลหุ้นกิน 10% -> 50%
        print_progress(f"ดึงข้อมูล {ticker} ({i}/{total})", pct)

    stock_results = fetch_all_stocks(progress_callback=on_fetch_progress)

    if not stock_results:
        print("❌ ดึงข้อมูลหุ้นไม่ได้เลยสักตัว ตรวจสอบการเชื่อมต่ออินเทอร์เน็ต แล้วลองใหม่")
        return

    print_progress(f"ดึงข้อมูลสำเร็จ {len(stock_results)}/{len(stock_results)} ตัว", 50)

    print_progress("กำลังดึงค่า Fear & Greed Index", 55)
    fear_greed = get_fear_greed()
    if fear_greed:
        print_progress(f"Fear & Greed Index = {fear_greed['value']} ({fear_greed['rating']})", 60)
    else:
        print("    ⚠️  ข้ามค่า Fear & Greed Index รอบนี้ (ดึงไม่สำเร็จ)")

    print_progress("กำลังวิเคราะห์ด้วย Gemini", 70)
    summary = analyze_stocks(stock_results, fear_greed)
    save_analysis(datetime.now().strftime("%Y-%m-%d"), summary)
    print_progress("วิเคราะห์เสร็จสิ้น", 90)

    if DISCORD_WEBHOOK_URL:
        print_progress("กำลังส่งเข้า Discord", 95)
        send_to_discord(DISCORD_WEBHOOK_URL, summary, len(stock_results), fear_greed)
    else:
        print("⚠️  ไม่ได้ตั้งค่า DISCORD_WEBHOOK_URL ใน .env — ข้ามการส่ง Discord")
        print("\n--- สรุปผลวิเคราะห์ ---")
        print(summary)

    print_progress("เสร็จสมบูรณ์", 100)
    print("=" * 50)


if __name__ == "__main__":
    main()

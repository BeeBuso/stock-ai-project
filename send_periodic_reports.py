"""
send_periodic_reports.py
ส่งรายงานสรุปผลรายสัปดาห์ / รายเดือน / อันดับ Top 10 เข้า Discord
แต่ละรายงานแยกกันเป็นการ์ดคนละใบ ไม่ปนกับรายงานรายวัน (ของเดิมไม่เปลี่ยนแปลง)

วิธีรัน:
  python send_periodic_reports.py weekly     -> ส่งเฉพาะรายสัปดาห์
  python send_periodic_reports.py monthly    -> ส่งเฉพาะรายเดือน
  python send_periodic_reports.py top10      -> ส่งเฉพาะอันดับ Top 10
  python send_periodic_reports.py all        -> ส่งทั้ง 3 ชุดรวดเดียว (คนละการ์ด)
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from performance_reports import generate_weekly_report, generate_monthly_report, generate_top10_report
from notify_discord import send_period_summary_report, send_top10_report

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def send_weekly():
    stats, trades = generate_weekly_report()
    send_period_summary_report(DISCORD_WEBHOOK_URL, stats, trades, "📅 สรุปผลรายสัปดาห์ (7 วันล่าสุด)", color=5793266)


def send_monthly():
    stats, trades = generate_monthly_report()
    send_period_summary_report(DISCORD_WEBHOOK_URL, stats, trades, "🗓️ สรุปผลรายเดือน (30 วันล่าสุด)", color=10181046)


def send_top10():
    ranking = generate_top10_report()
    send_top10_report(DISCORD_WEBHOOK_URL, ranking)


def main():
    if not DISCORD_WEBHOOK_URL:
        print("❌ ไม่พบ DISCORD_WEBHOOK_URL ใน .env กรุณาตั้งค่าก่อนรัน")
        return

    if len(sys.argv) < 2:
        print("ใช้งาน: python send_periodic_reports.py [weekly|monthly|top10|all]")
        return

    mode = sys.argv[1].lower()

    if mode == "weekly":
        send_weekly()
    elif mode == "monthly":
        send_monthly()
    elif mode == "top10":
        send_top10()
    elif mode == "all":
        send_weekly()
        send_monthly()
        send_top10()
    else:
        print(f"❌ ไม่รู้จักโหมด '{mode}' ใช้ได้แค่ weekly / monthly / top10 / all")


if __name__ == "__main__":
    main()

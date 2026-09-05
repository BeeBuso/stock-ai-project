"""
notify_discord.py (ฉบับ cloud — เฉพาะฟังก์ชันที่จำเป็นสำหรับรายงาน Day Trade)
"""

import requests
from datetime import datetime, timezone


def _format_trade_table(trades):
    if not trades:
        return "(ไม่มี)"

    header = f"{'Ticker':<7}{'Entry':>8}{'ราคาล่าสุด':>12}{'P/L%':>9}  สถานะ"
    lines = [header, "-" * len(header)]

    status_label = {
        "OPEN": "🟡 OPEN",
        "CLOSED_TP": "🟢 TP",
        "CLOSED_SL": "🔴 SL",
        "CLOSED_EOD": "⚪ EOD",
    }

    for t in trades:
        label = status_label.get(t["status"], t["status"])
        lines.append(
            f"{t['ticker']:<7}{t['entry_price']:>8.2f}{t['exit_price']:>12.2f}{t['pnl_pct']:>+8.2f}%  {label}"
        )

    return "```\n" + "\n".join(lines) + "\n```"


def send_trading_report(webhook_url, open_trades, closed_today):
    """ส่งรายงานสถานะออเดอร์จำลอง (Day Trade) เข้า Discord แบบตาราง"""
    wins = sum(1 for t in closed_today if t["status"] == "CLOSED_TP")
    losses = sum(1 for t in closed_today if t["status"] == "CLOSED_SL")
    eod = sum(1 for t in closed_today if t["status"] == "CLOSED_EOD")

    embed = {
        "title": f"☁️ Day Trade Simulator (GitHub Actions) — {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "description": "⚠️ นี่คือการจำลองเท่านั้น ไม่มีการซื้อขายจริงเกิดขึ้น | รันบน GitHub Actions",
        "color": 3066993,  # สีเขียว (แยกจากสีส้มของฝั่งพีซี ให้รู้ว่าคนละที่มา)
        "fields": [
            {"name": f"📂 ออเดอร์ที่เปิดอยู่ ({len(open_trades)})", "value": _format_trade_table(open_trades), "inline": False},
            {"name": f"📁 ปิดแล้ววันนี้ ({len(closed_today)}) — ✅ {wins}  ❌ {losses}  ⏰ {eod}", "value": _format_trade_table(closed_today), "inline": False},
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "ระบบ Stock AI — Day Trade Simulator บน GitHub Actions (Paper Trading)"},
    }

    payload = {"embeds": [embed]}
    resp = requests.post(webhook_url, json=payload, timeout=15)
    resp.raise_for_status()
    print("    ✅ ส่งรายงาน Day Trade เข้า Discord สำเร็จ")

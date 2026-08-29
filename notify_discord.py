"""
notify_discord.py
ส่งผลสรุปวิเคราะห์หุ้นเข้าช่อง Discord ผ่าน Webhook (ไม่ต้องสร้างบอทให้ยุ่งยาก)
"""

import requests
from datetime import datetime, timezone


def send_to_discord(webhook_url, summary_text, stock_count, fear_greed=None):
    """ส่งข้อความสรุปเป็น Discord embed สวยๆ เข้าช่องที่ตั้ง webhook ไว้ พร้อมฟิลด์ Fear & Greed Index แยกให้เห็นชัด"""
    embed = {
        "title": f"📊 สรุปหุ้นประจำวัน {datetime.now().strftime('%d/%m/%Y')}",
        "description": summary_text,
        "color": 3447003,  # สีฟ้า
        "footer": {"text": f"วิเคราะห์จากข้อมูล {stock_count} ตัว | ระบบ Stock AI"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if fear_greed:
        embed["fields"] = [
            {
                "name": f"😨😐🤑 Fear & Greed Index: {fear_greed['value']}/100 ({fear_greed['rating']})",
                "value": fear_greed["signal"],
                "inline": False,
            }
        ]
        if fear_greed["trend_text"]:
            embed["fields"].append({
                "name": "แนวโน้มดัชนี",
                "value": fear_greed["trend_text"],
                "inline": False,
            })

    payload = {"embeds": [embed]}

    resp = requests.post(webhook_url, json=payload, timeout=15)
    resp.raise_for_status()
    print("    ✅ ส่งเข้า Discord สำเร็จ")


def _format_trade_table(trades):
    """สร้างตารางข้อความ (monospace) สำหรับแสดงออเดอร์จำลอง"""
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
        "title": f"🧪 Day Trade Simulator — {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        "description": "⚠️ นี่คือการจำลองเท่านั้น ไม่มีการซื้อขายจริงเกิดขึ้น",
        "color": 15105570,  # สีส้ม
        "fields": [
            {"name": f"📂 ออเดอร์ที่เปิดอยู่ ({len(open_trades)})", "value": _format_trade_table(open_trades), "inline": False},
            {"name": f"📁 ปิดแล้ววันนี้ ({len(closed_today)}) — ✅ {wins}  ❌ {losses}  ⏰ {eod}", "value": _format_trade_table(closed_today), "inline": False},
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "ระบบ Stock AI — Day Trade Simulator (Paper Trading)"},
    }

    payload = {"embeds": [embed]}
    resp = requests.post(webhook_url, json=payload, timeout=15)
    resp.raise_for_status()
    print("    ✅ ส่งรายงาน Day Trade เข้า Discord สำเร็จ")


def send_period_summary_report(webhook_url, stats, trades, title, color=5793266):
    """ส่งรายงานสรุปช่วงเวลา (ใช้ได้ทั้งรายสัปดาห์/รายเดือน) พร้อมตัวเลขสรุป + ตารางรายการเทรดแต่ละไม้
    ตัวเลขสรุปใช้ embed fields ของ Discord เอง เพื่อให้จัดตำแหน่งตรงเป๊ะ ไม่ต้องพึ่งการนับความกว้างฟอนต์ไทยเอง"""
    embed = {
        "title": title,
        "color": color,
        "fields": [
            {"name": "ออเดอร์ทั้งหมด", "value": str(stats["total"]), "inline": True},
            {"name": "ชนะ (TP)", "value": str(stats["wins"]), "inline": True},
            {"name": "แพ้ (SL)", "value": str(stats["losses"]), "inline": True},
            {"name": "ปิดหมดวัน (EOD)", "value": str(stats["eod"]), "inline": True},
            {"name": "อัตราชนะ", "value": f"{stats['win_rate']}%", "inline": True},
            {"name": "กำไร/ขาดทุนรวม", "value": f"{stats['total_pnl']:+.2f}%", "inline": True},
            {"name": "เฉลี่ยต่อไม้", "value": f"{stats['avg_pnl']:+.2f}%", "inline": True},
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "ระบบ Stock AI — สรุปผล Day Trade Simulator (จำลอง ไม่ใช่เงินจริง)"},
    }

    if trades:
        MAX_ROWS = 15  # จำกัดจำนวนแถวกันข้อความยาวเกินลิมิตของ Discord (แสดงล่าสุดก่อน)
        recent = list(reversed(trades))[:MAX_ROWS]
        table = _format_trade_table(recent)
        if len(trades) > MAX_ROWS:
            table += f"\n(แสดง {MAX_ROWS} รายการล่าสุด จากทั้งหมด {len(trades)} รายการ)"
        embed["fields"].append({"name": f"📋 รายการเทรด ({len(trades)})", "value": table, "inline": False})

    payload = {"embeds": [embed]}
    resp = requests.post(webhook_url, json=payload, timeout=15)
    resp.raise_for_status()
    print(f"    ✅ ส่งรายงาน '{title}' เข้า Discord สำเร็จ")


def send_top10_report(webhook_url, ranking):
    """ส่งอันดับหุ้นทำกำไรสะสมสูงสุด-ต่ำสุด 10 อันดับ เป็นการ์ดแยกต่างหาก"""
    if not ranking:
        table = "(ยังไม่มีข้อมูลออเดอร์ที่ปิดแล้วในระบบ)"
    else:
        header = f"{'#':<3}{'Ticker':<8}{'กำไรสะสม':>12}{'ไม้':>6}{'Win%':>8}"
        lines = [header, "-" * len(header)]
        for i, r in enumerate(ranking, start=1):
            lines.append(f"{i:<3}{r['ticker']:<8}{r['total_pnl']:>+11.2f}%{r['count']:>6}{r['win_rate']:>7.1f}%")
        table = "```\n" + "\n".join(lines) + "\n```"

    embed = {
        "title": f"🏆 อันดับหุ้นทำกำไรสะสมสูงสุด (Top 10) — {datetime.now().strftime('%d/%m/%Y')}",
        "description": table,
        "color": 15844367,  # สีทอง
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {"text": "ระบบ Stock AI — จัดอันดับจากออเดอร์จำลองทั้งหมดตั้งแต่เริ่มใช้งาน"},
    }
    payload = {"embeds": [embed]}
    resp = requests.post(webhook_url, json=payload, timeout=15)
    resp.raise_for_status()
    print("    ✅ ส่งรายงาน Top 10 เข้า Discord สำเร็จ")

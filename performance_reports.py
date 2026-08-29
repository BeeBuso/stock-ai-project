"""
performance_reports.py
คำนวณสรุปผลระบบจำลองเทรด (Paper Trading) แยกเป็น 3 ชุด:
1. รายสัปดาห์ (ย้อนหลัง 7 วัน)
2. รายเดือน (ย้อนหลัง 30 วัน)
3. อันดับหุ้นทำกำไรสะสมสูงสุด-ต่ำสุด 10 อันดับ (นับตั้งแต่เริ่มใช้งานระบบ)

⚠️ ตัวเลขกำไร/ขาดทุน (%) เป็นผลรวมแบบบวกตรงๆ ต่อไม้ (ไม่ได้คิดทบต้น)
   ใช้เปรียบเทียบภาพรวมของกลยุทธ์เท่านั้น ไม่ใช่ผลตอบแทนพอร์ตจริง
"""

from datetime import datetime, timedelta
from collections import defaultdict

from database import get_closed_trades_since, get_all_closed_trades


def _summarize(trades):
    """สรุปสถิติภาพรวมจากลิสต์ออเดอร์ที่ปิดแล้ว"""
    total = len(trades)
    wins = sum(1 for t in trades if t["status"] == "CLOSED_TP")
    losses = sum(1 for t in trades if t["status"] == "CLOSED_SL")
    eod = sum(1 for t in trades if t["status"] == "CLOSED_EOD")
    total_pnl = sum(t["pnl_pct"] for t in trades)
    avg_pnl = round(total_pnl / total, 2) if total else 0
    win_rate = round(wins / (wins + losses) * 100, 1) if (wins + losses) else 0

    return {
        "total": total, "wins": wins, "losses": losses, "eod": eod,
        "total_pnl": round(total_pnl, 2), "avg_pnl": avg_pnl, "win_rate": win_rate,
    }


def generate_weekly_report():
    """สรุปผลย้อนหลัง 7 วัน คืนค่า (สถิติสรุป, ลิสต์ออเดอร์ดิบ)"""
    cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    trades = get_closed_trades_since(cutoff)
    return _summarize(trades), trades


def generate_monthly_report():
    """สรุปผลย้อนหลัง 30 วัน คืนค่า (สถิติสรุป, ลิสต์ออเดอร์ดิบ)"""
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    trades = get_closed_trades_since(cutoff)
    return _summarize(trades), trades


def generate_top10_report():
    """จัดอันดับหุ้นตามกำไร/ขาดทุนสะสม (%) มาก -> น้อย 10 อันดับแรก นับตั้งแต่เริ่มใช้งานระบบ"""
    trades = get_all_closed_trades()

    by_ticker = defaultdict(lambda: {"total_pnl": 0.0, "count": 0, "wins": 0})
    for t in trades:
        entry = by_ticker[t["ticker"]]
        entry["total_pnl"] += t["pnl_pct"]
        entry["count"] += 1
        if t["status"] == "CLOSED_TP":
            entry["wins"] += 1

    ranking = [
        {
            "ticker": ticker,
            "total_pnl": round(data["total_pnl"], 2),
            "count": data["count"],
            "win_rate": round(data["wins"] / data["count"] * 100, 1) if data["count"] else 0,
        }
        for ticker, data in by_ticker.items()
    ]
    ranking.sort(key=lambda x: x["total_pnl"], reverse=True)

    return ranking[:10]

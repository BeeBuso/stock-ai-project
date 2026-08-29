"""
day_trade_engine.py
แกนหลักของระบบจำลอง Day Trade (Paper Trading):
- เช็กว่าตลาดอเมริกาเปิดอยู่ไหม (อิงเวลานิวยอร์กจริง ไม่ใช่เวลาไทย)
- สแกนหุ้นใน watchlist หาสัญญาณ Breakout + Volume + RSI
- เปิดออเดอร์จำลอง ติดตามจนชน TP/SL หรือหมดวัน (Day Trade ต้องปิดก่อนตลาดปิด)

⚠️ นี่คือการจำลองเท่านั้น ไม่มีการส่งคำสั่งซื้อขายจริงไปยังโบรกเกอร์ใดๆ
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import yfinance as yf

from database import open_paper_trade, close_paper_trade, get_open_trades
from technical_analysis import calculate_pivot_points
from indicators import calculate_rsi, volume_ratio
from watchlist import DAY_TRADE_WATCHLIST
from fetch_data import fetch_ticker

NY_TZ = ZoneInfo("America/New_York")
MAX_CONCURRENT_TRADES = 5

# เกณฑ์สัญญาณเข้าออเดอร์ (Breakout + Volume + RSI) — ปรับตัวเลขเหล่านี้เพื่อทดสอบกลยุทธ์ต่างๆ ได้
MIN_VOLUME_RATIO = 1.3
RSI_MIN = 50
RSI_MAX = 75


def now_ny():
    return datetime.now(NY_TZ)


def today_ny_str():
    return now_ny().strftime("%Y-%m-%d")


def is_market_open():
    """เช็กว่าตอนนี้อยู่ในเวลาทำการตลาดหุ้นอเมริกาไหม (จันทร์-ศุกร์ 9:30-16:00 เวลานิวยอร์ก)"""
    n = now_ny()
    if n.weekday() >= 5:  # เสาร์=5, อาทิตย์=6
        return False
    open_time = n.replace(hour=9, minute=30, second=0, microsecond=0)
    close_time = n.replace(hour=16, minute=0, second=0, microsecond=0)
    return open_time <= n <= close_time


def is_near_market_close(minutes_before=10):
    """เช็กว่าใกล้ตลาดปิดหรือยัง (ใช้บังคับปิดออเดอร์ Day Trade ทั้งหมดก่อนหมดวัน)"""
    n = now_ny()
    close_time = n.replace(hour=16, minute=0, second=0, microsecond=0)
    return n >= close_time - timedelta(minutes=minutes_before)


def get_day_trade_signal(ticker):
    """
    ดึงข้อมูล 3 เดือนของหุ้น 1 ตัว คำนวณ Pivot + RSI + Volume Ratio
    คืนค่า dict สัญญาณถ้าเข้าเงื่อนไข Breakout หรือ None ถ้าไม่เข้าเงื่อนไข/ข้อมูลไม่พอ
    """
    try:
        hist = yf.Ticker(ticker).history(period="3mo")
        if hist.empty or len(hist) < 25:
            return None

        prev_day = hist.iloc[-2]
        today = hist.iloc[-1]
        current_price = round(float(today["Close"]), 2)
        current_volume = float(today["Volume"])

        levels = calculate_pivot_points(prev_day["High"], prev_day["Low"], prev_day["Close"])
        rsi = calculate_rsi(hist["Close"])
        avg_volume_20d = float(hist["Volume"].tail(20).mean())
        vol_ratio = volume_ratio(current_volume, avg_volume_20d)

        r1, r2, r3 = levels["resistance"]
        s1, s2, s3 = levels["support"]

        # เงื่อนไข Breakout: ราคาทะลุ R1 + วอลุ่มพุ่ง + RSI อยู่ในโซนขาขึ้นที่ยังไม่ overbought สุดขั้ว
        breakout = current_price > r1
        volume_confirmed = vol_ratio >= MIN_VOLUME_RATIO
        rsi_ok = rsi is not None and RSI_MIN <= rsi <= RSI_MAX

        if not (breakout and volume_confirmed and rsi_ok):
            return None

        return {
            "ticker": ticker,
            "entry_price": current_price,
            "tp1": r2, "tp2": r3, "tp3": round(r3 + (r3 - levels["pivot"]), 2),
            "sl1": r1, "sl2": levels["pivot"], "sl3": s1,
            "rsi": rsi,
            "volume_ratio": vol_ratio,
            "score": round(vol_ratio * 2 + (current_price - r1) / r1 * 100, 2),  # ยิ่งวอลุ่มพุ่ง+ทะลุแรง ยิ่งคะแนนสูง
        }
    except Exception as e:
        print(f"    ⚠️  สแกน {ticker} ไม่สำเร็จ: {e}")
        return None


def scan_and_open_new_trades():
    """สแกนหุ้นทั้ง watchlist หาตัวที่เข้าเงื่อนไขมากที่สุด แล้วเปิดออเดอร์จำลอง (ไม่เกิน MAX_CONCURRENT_TRADES พร้อมกัน)"""
    open_trades = get_open_trades()
    slots_available = MAX_CONCURRENT_TRADES - len(open_trades)
    if slots_available <= 0:
        print("    ℹ️  ออเดอร์เต็มโควตาแล้ว ข้ามการสแกนรอบนี้")
        return []

    already_trading = {t["ticker"] for t in open_trades}
    candidates = []

    for ticker in DAY_TRADE_WATCHLIST:
        if ticker in already_trading:
            continue
        signal = get_day_trade_signal(ticker)
        if signal:
            candidates.append(signal)

    candidates.sort(key=lambda s: s["score"], reverse=True)
    chosen = candidates[:slots_available]

    opened = []
    trade_date = today_ny_str()
    for sig in chosen:
        trade_id = open_paper_trade(
            ticker=sig["ticker"], trade_date=trade_date, entry_price=sig["entry_price"],
            tp1=sig["tp1"], tp2=sig["tp2"], tp3=sig["tp3"],
            sl1=sig["sl1"], sl2=sig["sl2"], sl3=sig["sl3"], score=sig["score"],
        )
        sig["id"] = trade_id
        opened.append(sig)
        print(f"    🟢 เปิดออเดอร์จำลอง {sig['ticker']} ที่ {sig['entry_price']} (คะแนน {sig['score']})")

    return opened


def check_and_close_trades():
    """เช็กออเดอร์ที่เปิดอยู่ทั้งหมด ปิดถ้าราคาปัจจุบันชน TP1 หรือ SL1"""
    open_trades = get_open_trades()
    updates = []

    for t in open_trades:
        data = fetch_ticker(t["ticker"])
        if not data:
            continue
        price = data["close_price"]

        if price >= t["tp1"]:
            pnl_pct = round((price - t["entry_price"]) / t["entry_price"] * 100, 2)
            close_paper_trade(t["id"], price, "CLOSED_TP", pnl_pct)
            print(f"    ✅ {t['ticker']} ชน TP1 ที่ {price} (+{pnl_pct}%)")
            updates.append({**t, "status": "CLOSED_TP", "exit_price": price, "pnl_pct": pnl_pct})
        elif price <= t["sl1"]:
            pnl_pct = round((price - t["entry_price"]) / t["entry_price"] * 100, 2)
            close_paper_trade(t["id"], price, "CLOSED_SL", pnl_pct)
            print(f"    🔴 {t['ticker']} ชน SL1 ที่ {price} ({pnl_pct}%)")
            updates.append({**t, "status": "CLOSED_SL", "exit_price": price, "pnl_pct": pnl_pct})
        else:
            pnl_pct = round((price - t["entry_price"]) / t["entry_price"] * 100, 2)
            updates.append({**t, "status": "OPEN", "exit_price": price, "pnl_pct": pnl_pct})

    return updates


def force_close_all_eod():
    """บังคับปิดออเดอร์ที่เหลือทั้งหมดตอนใกล้ตลาดปิด (กติกา Day Trade: ห้ามถือข้ามวัน)"""
    open_trades = get_open_trades()
    closed = []
    for t in open_trades:
        data = fetch_ticker(t["ticker"])
        price = data["close_price"] if data else t["entry_price"]
        pnl_pct = round((price - t["entry_price"]) / t["entry_price"] * 100, 2)
        close_paper_trade(t["id"], price, "CLOSED_EOD", pnl_pct)
        print(f"    ⏰ {t['ticker']} ปิดหมดวัน (EOD) ที่ {price} ({pnl_pct:+.2f}%)")
        closed.append({**t, "status": "CLOSED_EOD", "exit_price": price, "pnl_pct": pnl_pct})
    return closed

"""
fetch_data.py (ฉบับ cloud — เหมือนไฟล์เดิมที่พีซีทุกประการ)
ดึงราคาหุ้นจาก Yahoo Finance (yfinance) — ใช้ได้ทั้งหุ้นอเมริกาและหุ้นไทย
"""

import yfinance as yf


def fetch_ticker(ticker):
    """ดึงข้อมูลหุ้น 1 ตัว คืนค่า dict หรือ None ถ้าดึงไม่สำเร็จ"""
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="5d")

        if hist.empty or len(hist) < 2:
            return None

        latest = hist.iloc[-1]
        previous = hist.iloc[-2]
        close_price = round(float(latest["Close"]), 2)
        prev_close = float(previous["Close"])
        change_pct = round((close_price - prev_close) / prev_close * 100, 2)
        volume = int(latest["Volume"])
        date = hist.index[-1].strftime("%Y-%m-%d")

        return {
            "ticker": ticker,
            "date": date,
            "close_price": close_price,
            "change_pct": change_pct,
            "volume": volume,
        }
    except Exception as e:
        print(f"    ⚠️  ดึงข้อมูล {ticker} ไม่สำเร็จ: {e}")
        return None

"""
fetch_data.py
ดึงราคาหุ้นจาก Yahoo Finance (yfinance) — ใช้ได้ทั้งหุ้นอเมริกาและหุ้นไทย
หุ้นไทยใน yfinance ต้องเติม .BK ต่อท้าย เช่น PTT.BK, AOT.BK
"""

import yfinance as yf
from database import save_price

# 🔧 แก้ไขรายชื่อหุ้นที่อยากติดตามตรงนี้ได้เลย
US_TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL"]
TH_TICKERS = ["PTT.BK", "AOT.BK", "CPALL.BK", "ADVANC.BK", "KBANK.BK"]


def fetch_ticker(ticker):
    """ดึงข้อมูลหุ้น 1 ตัว คืนค่า dict หรือ None ถ้าดึงไม่สำเร็จ (เช่น ชื่อหุ้นผิด หรือเน็ตหลุด)"""
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


def fetch_all_stocks(progress_callback=None):
    """
    ดึงข้อมูลหุ้นทั้งหมด (ไทย + อเมริกา) แล้วบันทึกลงฐานข้อมูลทันทีทีละตัว
    progress_callback(i, total, ticker) จะถูกเรียกหลังดึงแต่ละตัวเสร็จ ใช้แสดง % ความคืบหน้า
    """
    all_tickers = US_TICKERS + TH_TICKERS
    results = []
    total = len(all_tickers)

    for i, ticker in enumerate(all_tickers, start=1):
        data = fetch_ticker(ticker)
        if data:
            save_price(**data)
            results.append(data)

        if progress_callback:
            progress_callback(i, total, ticker)

    return results

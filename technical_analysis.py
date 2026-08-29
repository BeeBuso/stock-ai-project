"""
technical_analysis.py
คำนวณแนวรับ-แนวต้าน และระดับ TP/SL จากข้อมูลราคาย้อนหลังจริง ด้วยสูตร Pivot Point แบบคลาสสิก (Floor Trader)

⚠️ นี่คือการคำนวณทางคณิตศาสตร์จากราคาที่เกิดขึ้นแล้ว ไม่ใช่การพยากรณ์อนาคต
   และไม่ใช่คำแนะนำการลงทุน เป็นเพียงเครื่องมือช่วยดูระดับราคาที่นักลงทุนสายเทคนิคนิยมใช้อ้างอิง
"""

import yfinance as yf


def calculate_pivot_points(high, low, close):
    """สูตร Pivot Point แบบคลาสสิก ใช้ราคาสูงสุด/ต่ำสุด/ปิดของวันก่อนหน้า"""
    pivot = (high + low + close) / 3
    r1 = 2 * pivot - low
    s1 = 2 * pivot - high
    r2 = pivot + (high - low)
    s2 = pivot - (high - low)
    r3 = high + 2 * (pivot - low)
    s3 = low - 2 * (high - pivot)

    return {
        "pivot": round(pivot, 2),
        "resistance": [round(r1, 2), round(r2, 2), round(r3, 2)],
        "support": [round(s1, 2), round(s2, 2), round(s3, 2)],
    }


def get_technical_levels(ticker, current_price):
    """
    ดึงราคาย้อนหลัง 3 เดือน มาคำนวณแนวรับ-แนวต้าน + จุดสังเกตระยะสั้น (swing high/low 20 วัน)
    คืนค่า dict พร้อมจุดเข้า/TP/SL ที่คำนวณได้ หรือ None ถ้าข้อมูลไม่พอ
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")

        if hist.empty or len(hist) < 2:
            return None

        prev_day = hist.iloc[-2]  # ใช้ราคาวันก่อนหน้าตามสูตร pivot point มาตรฐาน
        levels = calculate_pivot_points(prev_day["High"], prev_day["Low"], prev_day["Close"])

        recent = hist.tail(20)
        swing_high = round(float(recent["High"].max()), 2)
        swing_low = round(float(recent["Low"].min()), 2)

        # จุดเข้าที่น่าสนใจ (แนวคิดทั่วไป): แนวรับถัดไปที่อยู่ต่ำกว่าราคาปัจจุบัน
        supports_below = [s for s in levels["support"] if s < current_price]
        entry_zone = max(supports_below) if supports_below else levels["support"][0]

        return {
            "pivot": levels["pivot"],
            "resistance": levels["resistance"],   # ใช้เป็นแนว TP1, TP2, TP3
            "support": levels["support"],          # ใช้เป็นแนว SL1, SL2, SL3
            "swing_high_20d": swing_high,
            "swing_low_20d": swing_low,
            "entry_zone": entry_zone,
        }
    except Exception as e:
        print(f"    ⚠️  คำนวณแนวรับ-แนวต้าน {ticker} ไม่สำเร็จ: {e}")
        return None

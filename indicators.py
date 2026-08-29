"""
indicators.py
อินดิเคเตอร์เพิ่มเติมสำหรับกลยุทธ์ Day Trade (นอกเหนือจาก Pivot Point ที่มีอยู่แล้ว)
"""


def calculate_rsi(close_prices, period=14):
    """
    คำนวณ RSI (Relative Strength Index) จากราคาปิดย้อนหลัง (pandas Series)
    RSI > 70 = โซนซื้อมากเกินไป (Overbought) เสี่ยงราคากลับตัวลง
    RSI < 30 = โซนขายมากเกินไป (Oversold) เสี่ยงราคากลับตัวขึ้น
    คืนค่า None ถ้าข้อมูลไม่พอคำนวณ
    """
    if len(close_prices) < period + 1:
        return None

    delta = close_prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    last_avg_loss = avg_loss.iloc[-1]
    if last_avg_loss == 0:
        return 100.0  # ไม่มีวันขาดทุนเลยในช่วงนี้ ถือว่าโมเมนตัมขาขึ้นสุดขั้ว

    rs = avg_gain.iloc[-1] / last_avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi), 1)


def volume_ratio(current_volume, avg_volume_20d):
    """อัตราส่วนวอลุ่มปัจจุบันเทียบค่าเฉลี่ย 20 วัน (>1.3 ถือว่าวอลุ่มเริ่มพุ่งผิดปกติ)"""
    if not avg_volume_20d:
        return 0.0
    return round(current_volume / avg_volume_20d, 2)

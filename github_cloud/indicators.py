"""
indicators.py (ฉบับ cloud — เหมือนไฟล์เดิมที่พีซีทุกประการ)
"""


def calculate_rsi(close_prices, period=14):
    if len(close_prices) < period + 1:
        return None

    delta = close_prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    last_avg_loss = avg_loss.iloc[-1]
    if last_avg_loss == 0:
        return 100.0

    rs = avg_gain.iloc[-1] / last_avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi), 1)


def volume_ratio(current_volume, avg_volume_20d):
    if not avg_volume_20d:
        return 0.0
    return round(current_volume / avg_volume_20d, 2)

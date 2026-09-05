"""
technical_analysis.py (ฉบับ cloud — เหมือนไฟล์เดิมที่พีซีทุกประการ)
คำนวณแนวรับ-แนวต้าน ด้วยสูตร Pivot Point แบบคลาสสิก
"""


def calculate_pivot_points(high, low, close):
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

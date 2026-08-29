"""
fetch_fear_greed.py
ดึงค่า CNN Fear & Greed Index ปัจจุบัน แล้วแปลงเป็นสัญญาณจังหวะซื้อขายแบบ Contrarian
ตามหลักการของ Warren Buffett: "จงกลัวเมื่อคนอื่นโลภ และจงโลภเมื่อคนอื่นกลัว"
"""

import fear_and_greed
from database import save_fear_greed, get_previous_fear_greed


def classify_zone(value):
    """
    แบ่งโซนตามเกณฑ์มาตรฐาน (0-100) คืนค่า (ชื่อโซน, ข้อความสัญญาณซื้อ-ขาย)
    0-25   Extreme Fear  -> โซนซื้อ (Contrarian buy)
    75-100 Extreme Greed -> โซนขาย/ทำกำไร (Contrarian sell)
    """
    if value <= 25:
        return "Extreme Fear", (
            "🟢 โซนซื้อ (Extreme Fear) — ตลาดตื่นตระหนกจนราคาอาจต่ำกว่ามูลค่าที่ควรจะเป็น "
            "(Oversold) เป็นโอกาสพิจารณาเข้าเก็บสะสมตามหลัก Contrarian"
        )
    elif value <= 45:
        return "Fear", "🟡 โซนกลัว (Fear) — ยังไม่ถึงจุดสุดขั้ว ติดตามต่อเนื่อง"
    elif value <= 55:
        return "Neutral", "⚪ โซนกลาง (Neutral) — ตลาดยังไม่มีอารมณ์ไปทางใดทางหนึ่งชัดเจน"
    elif value <= 75:
        return "Greed", "🟡 โซนโลภ (Greed) — เริ่มร้อนแรง ระวังความเสี่ยงเพิ่มขึ้น"
    else:
        return "Extreme Greed", (
            "🔴 โซนขาย/ทำกำไร (Extreme Greed) — ตลาดโลภสุดขั้ว ราคาอาจแพงเกินจริง "
            "เป็นสัญญาณเตือนให้พิจารณาทยอยขายทำกำไรตามหลัก Contrarian"
        )


def get_fear_greed():
    """
    ดึงค่า Fear & Greed Index ปัจจุบัน บันทึกลงฐานข้อมูล
    คืนค่า dict พร้อมสัญญาณซื้อขาย และค่าครั้งก่อนหน้าไว้เทียบแนวโน้ม (หรือ None ถ้าดึงไม่สำเร็จ)
    """
    try:
        result = fear_and_greed.get()
        value = round(result.value, 1)
        rating, signal = classify_zone(value)
        date = result.last_update.strftime("%Y-%m-%d")

        previous = get_previous_fear_greed()  # ดึงค่าก่อนหน้ามาเทียบ ก่อนจะบันทึกค่าใหม่ทับ
        save_fear_greed(date, value, rating)

        trend_text = ""
        if previous:
            prev_date, prev_value, prev_rating = previous
            if value > prev_value:
                trend_text = f"ขยับขึ้นจาก {prev_value} ({prev_rating}) เมื่อ {prev_date} — โน้มไปทาง Greed มากขึ้น"
            elif value < prev_value:
                trend_text = f"ขยับลงจาก {prev_value} ({prev_rating}) เมื่อ {prev_date} — โน้มไปทาง Fear มากขึ้น"
            else:
                trend_text = f"ทรงตัวเท่าเดิมจากครั้งก่อน ({prev_date})"

        return {
            "value": value,
            "rating": rating,
            "signal": signal,
            "trend_text": trend_text,
            "updated_at": result.last_update.strftime("%Y-%m-%d %H:%M"),
        }
    except Exception as e:
        print(f"    ⚠️  ดึงค่า Fear & Greed Index ไม่สำเร็จ: {e}")
        return None

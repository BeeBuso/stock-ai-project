"""
analyze.py
เรียก Gemini API มาวิเคราะห์ข้อมูลหุ้นที่ดึงมา โดยเอาผลวิเคราะห์ครั้งก่อนๆ มาให้ดูด้วย
(นี่คือกลไก 'ไม่ลืมข้อมูลเดิม' — ส่ง context ย้อนหลังเข้าไปในทุกครั้งที่วิเคราะห์)
"""

import os
import time
from google import genai
from database import get_past_analysis

# อ่าน GEMINI_API_KEY จาก environment variable
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# โมเดล Flash-Lite: โควตาฟรีสูงกว่า Flash ธรรมดามาก (~1,000 ครั้ง/วัน แทนที่จะเป็น ~20 ครั้ง/วัน)
# ใช้ alias "-latest" เพื่อให้ชี้ไปรุ่นล่าสุดที่ Google แนะนำเสมอ กันปัญหาชื่อรุ่นเปลี่ยน/หมดอายุ
MODEL = "gemini-flash-lite-latest"


def _call_gemini(prompt, max_retries=2, wait_seconds=45):
    """
    เรียก Gemini พร้อม retry อัตโนมัติเมื่อเจอ rate limit (429 / quota exceeded)
    Free Tier มีโควตาจำกัดต่อนาที ถ้าทดสอบถี่ๆ อาจชนขีดจำกัดชั่วคราว รอสักครู่แล้วลองใหม่ก็ผ่าน
    """
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            interaction = client.interactions.create(model=MODEL, input=prompt)
            return interaction.output_text
        except Exception as e:
            last_error = e
            is_rate_limit = "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "quota" in str(e).lower()
            if is_rate_limit and attempt < max_retries:
                print(f"    ⏳ โควตา Gemini เต็มชั่วคราว รอ {wait_seconds} วินาทีแล้วลองใหม่ ({attempt + 1}/{max_retries}) ...")
                time.sleep(wait_seconds)
                continue
            raise
    raise last_error


def build_prompt(stock_results, fear_greed=None):
    """แปลงข้อมูลหุ้นดิบ + Fear & Greed Index ให้เป็น prompt ข้อความสำหรับส่งให้ Gemini"""
    lines = []
    for r in stock_results:
        lines.append(
            f"- {r['ticker']}: ปิดที่ {r['close_price']} เปลี่ยนแปลง {r['change_pct']:+.2f}% "
            f"(วันที่ {r['date']}, ปริมาณซื้อขาย {r['volume']:,})"
        )
    data_text = "\n".join(lines)

    past = get_past_analysis(limit=2)
    past_text = ""
    if past:
        past_text = "\n\nสรุปวิเคราะห์ครั้งก่อนหน้า (ใช้อ้างอิงแนวโน้ม):\n"
        for date, summary in past:
            past_text += f"[{date}] {summary[:200]}...\n"

    fg_text = ""
    if fear_greed:
        fg_text = (
            f"\n\nCNN Fear & Greed Index ปัจจุบัน: {fear_greed['value']}/100 "
            f"({fear_greed['rating']})\n"
            f"สัญญาณ Contrarian: {fear_greed['signal']}\n"
        )
        if fear_greed["trend_text"]:
            fg_text += f"แนวโน้มดัชนี: {fear_greed['trend_text']}\n"

    prompt = f"""นี่คือข้อมูลราคาหุ้นล่าสุด (ตลาดไทยและอเมริกา):

{data_text}
{past_text}
{fg_text}

กรุณาวิเคราะห์และสรุปเป็นภาษาไทย โดย:
1. ชี้ตัวที่เคลื่อนไหวผิดปกติ (ขึ้น/ลงแรง) พร้อมเหตุผลคร่าวๆ ถ้าพอเดาได้จากตัวเลข
2. เทียบกับแนวโน้มจากผลวิเคราะห์ครั้งก่อนถ้ามีข้อมูล
3. ถ้ามีข้อมูล Fear & Greed Index ให้พูดถึงโซนปัจจุบันและความหมายเชิง Contrarian สั้นๆ ด้วย
4. สรุปภาพรวม 3-5 บรรทัด สั้น กระชับ อ่านง่าย เหมาะเอาไปโพสต์ใน Discord
5. อย่าให้คำแนะนำซื้อ-ขายฟันธง ให้เป็นการรายงานข้อมูลและสัญญาณเชิงวิเคราะห์เท่านั้น ผู้อ่านตัดสินใจเอง"""

    return prompt


def analyze_stocks(stock_results, fear_greed=None):
    """ส่งข้อมูลหุ้น + Fear & Greed Index ให้ Gemini วิเคราะห์ (มี retry อัตโนมัติถ้าเจอ rate limit)"""
    prompt = build_prompt(stock_results, fear_greed)
    return _call_gemini(prompt)


def analyze_single_stock(stock_data, technical=None):
    """
    วิเคราะห์หุ้นตัวเดียวแบบสั้นๆ — ใช้ตอบคำสั่ง /stock จากบอท Discord
    (ต่างจาก analyze_stocks ที่วิเคราะห์รวมหลายตัวพร้อมกันสำหรับรายงานประจำวัน)
    """
    tech_text = ""
    if technical:
        tech_text = f"""

ข้อมูลเชิงเทคนิค (คำนวณจากราคาย้อนหลังจริง ด้วยสูตร Pivot Point):
- แนวรับ (Support): {technical['support']}
- แนวต้าน (Resistance): {technical['resistance']}
- จุด Pivot: {technical['pivot']}
- Swing High/Low 20 วันล่าสุด: {technical['swing_high_20d']} / {technical['swing_low_20d']}
- จุดเข้าที่น่าสนใจ (แนวรับถัดไปจากราคาปัจจุบัน): {technical['entry_zone']}"""

    prompt = f"""หุ้น {stock_data['ticker']} ปิดที่ {stock_data['close_price']} เปลี่ยนแปลง {stock_data['change_pct']:+.2f}% \
(วันที่ {stock_data['date']}, ปริมาณซื้อขาย {stock_data['volume']:,}){tech_text}

กรุณาวิเคราะห์เป็นภาษาไทย:
1. การเคลื่อนไหวนี้ถือว่าปกติหรือผิดปกติเมื่อเทียบกับวอลุ่มซื้อขาย 2-3 บรรทัด
2. ถ้ามีข้อมูลเชิงเทคนิค ให้อธิบายสั้นๆ ว่าราคาปัจจุบันอยู่ตรงไหนเทียบกับแนวรับ-แนวต้าน
3. ปิดท้ายด้วยประโยคย้ำว่านี่คือค่าที่คำนวณจากราคาย้อนหลัง ไม่ใช่การพยากรณ์หรือคำแนะนำการลงทุน ผู้อ่านต้องประเมินความเสี่ยงเอง"""

    return _call_gemini(prompt)

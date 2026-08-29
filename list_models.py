"""
list_models.py
สคริปต์เช็กว่า Gemini API key ของคุณใช้เรียกโมเดลอะไรได้บ้าง (generateContent)
รันไฟล์นี้ก่อน เพื่อดูชื่อโมเดลที่ถูกต้อง แล้วเอาไปใส่ใน analyze.py
"""

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

print("โมเดลที่ key ของคุณเรียกใช้ generateContent (ข้อความ) ได้:\n")

for model in client.models.list():
    actions = getattr(model, "supported_actions", None) or []
    if "generateContent" in actions:
        print(f"  - {model.name}")

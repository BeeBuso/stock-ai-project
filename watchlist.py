"""
watchlist.py
รายชื่อหุ้นอเมริกาสภาพคล่องสูง ~25 ตัว สำหรับสแกนหาสัญญาณ Day Trade
เลือกกระจายหลายกลุ่มอุตสาหกรรม แก้ไข/เพิ่ม-ลดรายชื่อได้ตามต้องการ
"""

DAY_TRADE_WATCHLIST = [
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN",   # Big Tech
    "META", "TSLA", "AMD", "NFLX", "CRM",      # Tech / Growth
    "JPM", "BAC", "GS",                          # การเงิน
    "XOM", "CVX",                                 # พลังงาน
    "WMT", "HD", "COST",                          # ค้าปลีก
    "DIS", "KO", "PEP",                           # Consumer
    "INTC", "CSCO", "ORCL", "QCOM",               # Tech อื่นๆ
]

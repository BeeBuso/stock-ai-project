"""
discord_bot.py
บอท Discord แบบสองทาง — พิมพ์คำสั่งในช่อง Discord แล้วให้ระบบไปดึง/วิเคราะห์หุ้นให้ทันที

ต่างจาก main.py (ซึ่งเป็นการ "ส่งเข้า" Discord ทางเดียวตามเวลาที่ตั้งไว้)
ไฟล์นี้ต้องรันค้างไว้ตลอดเวลาเพื่อรอฟังคำสั่งจากผู้ใช้ (persistent process)
ถ้าปิดหน้าต่างนี้ บอทจะออฟไลน์ทันที

คำสั่งที่ใช้ได้ในดิสคอร์ด (พิมพ์ / แล้วเลือกจากเมนู):
  /stock ticker:AAPL        -> สรุปวิเคราะห์หุ้นตัวเดียวทันที
  /marketupdate             -> รันสรุปตลาดรวมทุกตัวทันที (เหมือนรายงานประจำวัน)
  /weeklyreport             -> สรุปผล Day Trade Simulator ย้อนหลัง 7 วัน
  /monthlyreport            -> สรุปผล Day Trade Simulator ย้อนหลัง 30 วัน
  /top10report              -> อันดับหุ้นทำกำไรสะสมสูงสุด 10 อันดับ

วิธีรัน:  python discord_bot.py
"""

import os
import asyncio
from datetime import datetime

import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()  # ต้องโหลดก่อน import ไฟล์อื่นเสมอ

from database import init_db, save_analysis
from fetch_data import fetch_ticker, fetch_all_stocks
from fetch_fear_greed import get_fear_greed
from technical_analysis import get_technical_levels
from analyze import analyze_stocks, analyze_single_stock
from performance_reports import generate_weekly_report, generate_monthly_report, generate_top10_report
from notify_discord import _format_trade_table

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
discord_client = discord.Client(intents=intents)
tree = app_commands.CommandTree(discord_client)


@discord_client.event
async def on_ready():
    init_db()
    await tree.sync()  # ลงทะเบียนคำสั่ง / กับ Discord (ครั้งแรกอาจใช้เวลาสักครู่กว่าจะขึ้น)
    print(f"✅ บอทออนไลน์แล้วในชื่อ {discord_client.user}")
    print("   พิมพ์ /stock หรือ /marketupdate ในช่อง Discord ที่เชิญบอทเข้าไปได้เลย")


@tree.command(name="stock", description="สรุปวิเคราะห์หุ้นตัวเดียวแบบทันที")
@app_commands.describe(ticker="ชื่อย่อหุ้น เช่น AAPL หรือหุ้นไทยต้องเติม .BK เช่น PTT.BK")
async def stock_command(interaction: discord.Interaction, ticker: str):
    await interaction.response.defer()  # กันไทม์เอาต์ระหว่างรอดึงข้อมูล+ให้ Gemini คิด

    try:
        print(f"[/stock] กำลังดึงข้อมูล {ticker} ...")
        data = await asyncio.to_thread(fetch_ticker, ticker.upper())
        if not data:
            await interaction.followup.send(
                f"❌ ดึงข้อมูล `{ticker}` ไม่สำเร็จ ตรวจสอบชื่อย่ออีกครั้ง (หุ้นไทยต้องเติม `.BK` เช่น `PTT.BK`)"
            )
            return

        print(f"[/stock] ดึงข้อมูลสำเร็จ กำลังคำนวณแนวรับ-แนวต้าน ...")
        technical = await asyncio.to_thread(get_technical_levels, data["ticker"], data["close_price"])

        print(f"[/stock] กำลังส่งให้ Gemini วิเคราะห์ ...")
        summary = await asyncio.to_thread(analyze_single_stock, data, technical)

        embed = discord.Embed(
            title=f"📈 {data['ticker']}",
            description=summary,
            color=0x3498DB,
            timestamp=datetime.now(),
        )
        embed.add_field(name="ราคาปิด", value=str(data["close_price"]), inline=True)
        embed.add_field(name="เปลี่ยนแปลง", value=f"{data['change_pct']:+.2f}%", inline=True)
        embed.add_field(name="วอลุ่ม", value=f"{data['volume']:,}", inline=True)

        if technical:
            embed.add_field(name="🎯 จุดเข้าที่น่าสนใจ", value=str(technical["entry_zone"]), inline=True)
            tp1, tp2, tp3 = technical["resistance"]
            sl1, sl2, sl3 = technical["support"]
            embed.add_field(
                name="TP (แนวต้าน)",
                value=f"TP1: {tp1}\nTP2: {tp2}\nTP3: {tp3}",
                inline=True,
            )
            embed.add_field(
                name="SL (แนวรับ)",
                value=f"SL1: {sl1}\nSL2: {sl2}\nSL3: {sl3}",
                inline=True,
            )
            embed.add_field(
                name="Swing High/Low (20 วัน)",
                value=f"สูงสุด {technical['swing_high_20d']} / ต่ำสุด {technical['swing_low_20d']}",
                inline=False,
            )
            embed.set_footer(text="⚠️ คำนวณจากราคาย้อนหลังด้วยสูตร Pivot Point ไม่ใช่การพยากรณ์หรือคำแนะนำการลงทุน")

        await interaction.followup.send(embed=embed)
        print(f"[/stock] ส่งผลลัพธ์สำเร็จ")

    except Exception as e:
        print(f"[/stock] ❌ เกิด error: {type(e).__name__}: {e}")
        if "429" in str(e) or "quota" in str(e).lower():
            await interaction.followup.send("⏳ Gemini โควตาฟรีเต็มชั่วคราว (ใช้บ่อยเกินไปในนาทีนี้) รออีกสักครู่ค่อยลองใหม่นะครับ")
        else:
            await interaction.followup.send(f"❌ เกิดข้อผิดพลาด: `{type(e).__name__}: {e}`")


@tree.command(name="marketupdate", description="รันสรุปตลาดรวมทุกตัวทันที (เหมือนรายงานประจำวัน)")
async def marketupdate_command(interaction: discord.Interaction):
    await interaction.response.defer()

    try:
        print("[/marketupdate] กำลังดึงข้อมูลหุ้นทั้งหมด ...")
        stock_results = await asyncio.to_thread(fetch_all_stocks)
        if not stock_results:
            await interaction.followup.send("❌ ดึงข้อมูลหุ้นไม่สำเร็จเลยสักตัว ลองใหม่อีกครั้ง")
            return

        print("[/marketupdate] ดึงค่า Fear & Greed Index ...")
        fear_greed = await asyncio.to_thread(get_fear_greed)

        print("[/marketupdate] กำลังส่งให้ Gemini วิเคราะห์ ...")
        summary = await asyncio.to_thread(analyze_stocks, stock_results, fear_greed)
        save_analysis(datetime.now().strftime("%Y-%m-%d"), summary)

        embed = discord.Embed(
            title="📊 สรุปตลาดตามคำสั่ง",
            description=summary,
            color=0x3498DB,
            timestamp=datetime.now(),
        )
        if fear_greed:
            embed.add_field(
                name=f"😨😐🤑 Fear & Greed Index: {fear_greed['value']}/100 ({fear_greed['rating']})",
                value=fear_greed["signal"],
                inline=False,
            )
        embed.set_footer(text=f"วิเคราะห์จากข้อมูล {len(stock_results)} ตัว | ระบบ Stock AI")

        await interaction.followup.send(embed=embed)
        print("[/marketupdate] ส่งผลลัพธ์สำเร็จ")

    except Exception as e:
        print(f"[/marketupdate] ❌ เกิด error: {type(e).__name__}: {e}")
        if "429" in str(e) or "quota" in str(e).lower():
            await interaction.followup.send("⏳ Gemini โควตาฟรีเต็มชั่วคราว (ใช้บ่อยเกินไปในนาทีนี้) รออีกสักครู่ค่อยลองใหม่นะครับ")
        else:
            await interaction.followup.send(f"❌ เกิดข้อผิดพลาด: `{type(e).__name__}: {e}`")


@tree.command(name="weeklyreport", description="สรุปผล Day Trade Simulator ย้อนหลัง 7 วัน")
async def weeklyreport_command(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        stats, trades = await asyncio.to_thread(generate_weekly_report)
        embed = discord.Embed(title="📅 สรุปผลรายสัปดาห์ (7 วันล่าสุด)", color=0x5865F2, timestamp=datetime.now())
        embed.add_field(name="ออเดอร์ทั้งหมด", value=str(stats["total"]), inline=True)
        embed.add_field(name="ชนะ (TP)", value=str(stats["wins"]), inline=True)
        embed.add_field(name="แพ้ (SL)", value=str(stats["losses"]), inline=True)
        embed.add_field(name="ปิดหมดวัน (EOD)", value=str(stats["eod"]), inline=True)
        embed.add_field(name="อัตราชนะ", value=f"{stats['win_rate']}%", inline=True)
        embed.add_field(name="กำไร/ขาดทุนรวม", value=f"{stats['total_pnl']:+.2f}%", inline=True)
        embed.add_field(name="เฉลี่ยต่อไม้", value=f"{stats['avg_pnl']:+.2f}%", inline=True)
        if trades:
            recent = list(reversed(trades))[:15]
            table = _format_trade_table(recent)
            if len(trades) > 15:
                table += f"\n(แสดง 15 รายการล่าสุด จากทั้งหมด {len(trades)} รายการ)"
            embed.add_field(name=f"📋 รายการเทรด ({len(trades)})", value=table, inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ เกิดข้อผิดพลาด: `{type(e).__name__}: {e}`")


@tree.command(name="monthlyreport", description="สรุปผล Day Trade Simulator ย้อนหลัง 30 วัน")
async def monthlyreport_command(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        stats, trades = await asyncio.to_thread(generate_monthly_report)
        embed = discord.Embed(title="🗓️ สรุปผลรายเดือน (30 วันล่าสุด)", color=0x9B59B6, timestamp=datetime.now())
        embed.add_field(name="ออเดอร์ทั้งหมด", value=str(stats["total"]), inline=True)
        embed.add_field(name="ชนะ (TP)", value=str(stats["wins"]), inline=True)
        embed.add_field(name="แพ้ (SL)", value=str(stats["losses"]), inline=True)
        embed.add_field(name="ปิดหมดวัน (EOD)", value=str(stats["eod"]), inline=True)
        embed.add_field(name="อัตราชนะ", value=f"{stats['win_rate']}%", inline=True)
        embed.add_field(name="กำไร/ขาดทุนรวม", value=f"{stats['total_pnl']:+.2f}%", inline=True)
        embed.add_field(name="เฉลี่ยต่อไม้", value=f"{stats['avg_pnl']:+.2f}%", inline=True)
        if trades:
            recent = list(reversed(trades))[:15]
            table = _format_trade_table(recent)
            if len(trades) > 15:
                table += f"\n(แสดง 15 รายการล่าสุด จากทั้งหมด {len(trades)} รายการ)"
            embed.add_field(name=f"📋 รายการเทรด ({len(trades)})", value=table, inline=False)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ เกิดข้อผิดพลาด: `{type(e).__name__}: {e}`")


@tree.command(name="top10report", description="อันดับหุ้นทำกำไรสะสมสูงสุด 10 อันดับ")
async def top10report_command(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        ranking = await asyncio.to_thread(generate_top10_report)
        if not ranking:
            await interaction.followup.send("ยังไม่มีข้อมูลออเดอร์ที่ปิดแล้วในระบบครับ")
            return

        lines = [f"{'#':<3}{'Ticker':<8}{'กำไรสะสม':>12}{'ไม้':>6}{'Win%':>8}", "-" * 37]
        for i, r in enumerate(ranking, start=1):
            lines.append(f"{i:<3}{r['ticker']:<8}{r['total_pnl']:>+11.2f}%{r['count']:>6}{r['win_rate']:>7.1f}%")

        embed = discord.Embed(
            title="🏆 อันดับหุ้นทำกำไรสะสมสูงสุด (Top 10)",
            description="```\n" + "\n".join(lines) + "\n```",
            color=0xF1C40F,
            timestamp=datetime.now(),
        )
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"❌ เกิดข้อผิดพลาด: `{type(e).__name__}: {e}`")


if __name__ == "__main__":
    if not BOT_TOKEN:
        print("❌ ไม่พบ DISCORD_BOT_TOKEN ใน .env กรุณาตั้งค่าก่อนรัน (ดูวิธีใน README.md)")
    else:
        discord_client.run(BOT_TOKEN)

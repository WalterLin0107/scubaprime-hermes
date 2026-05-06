from fastapi import FastAPI, Request
import os
import telegram
import asyncio
import time
from openai import AsyncOpenAI
import anthropic
import google.generativeai as genai

app = FastAPI()

# ---------- 环境变量 ----------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# 初始化客户端
bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY, timeout=30.0)
claude_client = anthropic.AsyncAnthropic(api_key=CLAUDE_API_KEY)
genai.configure(api_key=GEMINI_API_KEY)

# ---------- 工具函数：发 Telegram 消息 ----------
async def send_tg(text: str):
    try:
        await bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=text,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
    except Exception as e:
        print("TG send error:", e)

# ---------- 1. 接收 n8n 发来的任务 ----------
@app.post("/webhook/n8n")
async def n8n_webhook(request: Request):
    """n8n 触发：拉完数据→发这里→Hermes调度Agent"""
    task = await request.json()
    t = task.get("task_type")
    p = task.get("payload", {})
    print("Received task:", t)

    if t == "inventory_daily":
        await send_tg(f"📦 库存日报（Claude处理中）\nSKU数：{p.get('sku_count', 0)}\n处理时间：{time.ctime()}")
    elif t == "new_review":
        await send_tg(f"⭐ 新Review（GPT处理中）\n内容：{p.get('content', '')[:100]}...")
    elif t == "seller_monitor":
        await send_tg(f"🚨 跟卖告警（Gemini处理中）\n卖家：{p.get('seller', '')}\n价格：{p.get('price', 0)}")

    return {"status":"ok","msg":"task received"}

# ---------- 2. 你在 Telegram 发指令给 Hermes ----------
@app.post("/webhook/tg")
async def tg_webhook(request: Request):
    data = await request.json()
    msg = data.get("message", {}).get("text", "")
    chat_id = data.get("message", {}).get("chat", {}).get("id")

    if msg == "/start":
        await send_tg("✅ Hermes 已上线！（美国弗吉尼亚节点）\n可用指令：\n/inventory - 查询库存\n/replenish - 重新计算补货\n/report - 今日简报\n/help - 查看所有指令")
    elif msg == "/inventory":
        await send_tg("📊 正在查询实时库存...（对接SPAPI后返回真实数据）")
    elif msg == "/replenish":
        await send_tg("🧮 正在重新计算补货建议...")
    elif msg == "/report":
        await send_tg("📈 正在生成今日运营简报...")
    elif msg == "/help":
        await send_tg("📋 指令列表：\n/start - 查看状态\n/inventory - 查询库存\n/replenish - 重新计算补货\n/report - 今日简报\n/help - 查看指令列表")

    return {"ok": True}

# ---------- 3. 健康检查（n8n/UptimeRobot 可ping） ----------
@app.get("/")
def root():
    return {
        "service":"scuba-prime-hermes",
        "status":"running",
        "server_region":"US-Virginia",
        "timestamp": time.ctime()
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
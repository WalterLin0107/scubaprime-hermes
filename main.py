from fastapi import FastAPI, Request
from pydantic import BaseModel
import os
import asyncio
import time

app = FastAPI()

# ---------- 环境变量 ----------
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ---------- 工具函数：发 Telegram 消息 ----------
async def send_tg(text: str):
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        print("TG send error:", e)

# ---------- 数据模型 ----------
class N8nTask(BaseModel):
    task_type: str
    payload: dict

# ---------- 1. 接收 n8n 任务 ----------
@app.post("/webhook/n8n")
async def n8n_webhook(task: N8nTask):
    t = task.task_type
    p = task.payload

    if t == "inventory_daily":
        await send_tg(f"✅ 库存日报已接收\nSKU: {p.get('sku_count')}")
    elif t == "new_review":
        await send_tg(f"⭐ 新评论\n{p.get('content')[:100]}...")
    elif t == "seller_monitor":
        await send_tg(f"🚨 发现跟卖\n{p.get('seller')}")

    return {"status": "ok"}

# ---------- 2. Telegram 指令 ----------
@app.post("/webhook/tg")
async def tg_webhook(request: Request):
    data = await request.json()
    msg = data.get("message", {}).get("text", "")

    if msg == "/start":
        await send_tg("✅ Hermes 运行中（US Virginia）\n指令：/inventory /replenish /report")
    elif msg == "/inventory":
        await send_tg("📦 查询库存...")
    elif msg == "/replenish":
        await send_tg("🧮 计算补货...")
    elif msg == "/report":
        await send_tg("📈 生成日报...")
    return {"ok": True}

# ---------- 健康检查 ----------
@app.get("/")
def root():
    return {"status": "running", "region": "US-Virginia"}

import os
import aiohttp
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select, insert
from typing import List, Dict
from .database import notification_preferences, database, subscriptions

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                await connection.send_json(message)

    async def broadcast(self, message: dict, tier: str = None):
        for user_id, connections in self.active_connections.items():
            if tier:
                sub = await self.get_user_tier(user_id)
                if sub != tier:
                    continue
            for connection in connections:
                await connection.send_json(message)

    async def get_user_tier(self, user_id: int) -> str:
        query = select(subscriptions).where(subscriptions.c.user_id == user_id)
        result = await database.fetch_one(query)
        return result["tier"] if result else "free"

manager = ConnectionManager()

async def send_telegram_message(chat_id: str, message: str):
    if not TELEGRAM_BOT_TOKEN:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            return await response.json()

async def notify_new_signal(signal_data: dict):
    await manager.broadcast({"type": "new_signal", "data": signal_data})

    query = select(notification_preferences).where(
        (notification_preferences.c.channel == "telegram") &
        (notification_preferences.c.enabled == True)
    )
    users = await database.fetch_all(query)

    message = f"""🚨 <b>New Trading Signal</b>

📊 <b>{signal_data['asset']}</b> | {signal_data['direction']}
💰 Entry: {signal_data['entry_price']}
🛑 SL: {signal_data['stop_loss']}
🎯 TP: {signal_data['take_profit']}

<a href='https://yourapp.com/#/signals/{signal_data['id']}'>View in App</a>"""

    for user in users:
        if user["telegram_chat_id"]:
            await send_telegram_message(user["telegram_chat_id"], message)

async def setup_telegram_webhook():
    if not TELEGRAM_BOT_TOKEN:
        return

    webhook_url = "https://yourapi.com/notifications/telegram/webhook"
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook"

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={"url": webhook_url}) as response:
            return await response.json()

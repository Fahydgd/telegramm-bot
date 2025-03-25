import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # URL для вебхука
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", 8080))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Хранилище персональных ссылок
user_links = {}

@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    user_links[user_id] = f"https://t.me/{bot.username}?start={user_id}"
    await message.answer(f"Привет! Вот твоя персональная ссылка: {user_links[user_id]}\n" 
                         "Люди могут писать тебе анонимно, а ты можешь отвечать им.")

@dp.message()
async def receive_anonymous_message(message: Message):
    if message.text and message.text.startswith("/start"):
        return  # Пропускаем обработку команды /start
    
    sender_id = message.from_user.id
    target_id = None
    
    if sender_id in user_links:
        target_id = sender_id
    
    if target_id:
        forward_text = f"💌 Анонимное сообщение для {target_id}:

{message.text or '[медиа]'}"
        await bot.send_message(target_id, forward_text)
        await bot.send_message(ADMIN_ID, f"👀 {message.from_user.full_name} (@{message.from_user.username}) написал: {message.text}")
    else:
        await message.answer("❌ Ошибка: получатель не найден.")

@dp.callback_query()
async def reply_to_anonymous(callback: types.CallbackQuery):
    target_id = callback.data.split(':')[1]
    await bot.send_message(target_id, f"✉️ Ответ на ваше сообщение: {callback.message.text}")
    await bot.send_message(ADMIN_ID, f"✅ Ответ отправлен пользователю {target_id}.")

async def on_startup():
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)

async def on_shutdown():
    await bot.delete_webhook()

async def main():
    logging.basicConfig(level=logging.INFO)
    app = web.Application()
    handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, on_startup=on_startup, on_shutdown=on_shutdown)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, HOST, PORT)
    await site.start()
    
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())

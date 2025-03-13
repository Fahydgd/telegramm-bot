import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import os

TOKEN = "7743030157:AAHUdBAbjgADXfpfFIjTXsS6OSzIbWX-5Rk"
ADMIN_ID = 1946338633  # Твой Telegram ID
WEBHOOK_URL = "https://your-app.onrender.com/webhook"
WEBHOOK_PATH = "/webhook"

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
user_messages = {}  # Сохраняем сообщения, чтобы можно было отвечать

@dp.message(CommandStart())
async def start_command(message: Message):
    await message.answer("Отправь мне анонимное сообщение, и его получит админ.")

@dp.message()
async def anonymous_message(message: Message):
    user_messages[message.message_id] = message.from_user.id
    forward_text = f"📩 Новое анонимное сообщение:\n{message.text}"
    reply_markup = types.InlineKeyboardMarkup()
    reply_markup.add(types.InlineKeyboardButton("Ответить", callback_data=f"reply_{message.message_id}"))
    await bot.send_message(ADMIN_ID, forward_text, reply_markup=reply_markup)
    await message.answer("✅ Сообщение отправлено анонимно.")

@dp.callback_query(lambda c: c.data.startswith("reply_"))
async def reply_callback(callback: types.CallbackQuery):
    msg_id = int(callback.data.split("_")[1])
    await bot.send_message(ADMIN_ID, "✍️ Напишите ответ на это сообщение:")
    dp.message.register(reply_handler, state=msg_id)

async def reply_handler(message: Message, state):
    user_id = user_messages.get(state)
    if user_id:
        await bot.send_message(user_id, f"📩 Ответ от админа:\n{message.text}")
        await message.answer("✅ Ответ отправлен.")
    else:
        await message.answer("❌ Ошибка: не найдено оригинальное сообщение.")
    dp.message.unregister(state)

async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown():
    await bot.delete_webhook()
    await bot.session.close()

app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
setup_application(app, dp, bot=bot)
app.on_startup.append(lambda _: on_startup())
app.on_shutdown.append(lambda _: on_shutdown())

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

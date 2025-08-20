from telegram import Bot
from telegram.ext import Application
from utils.config import get_settings
from utils.logging_config import system_logging
import httpx
from clients.tg_handlers import register_handlers

system_logging("INFO")
settings = get_settings()

TELEGRAM_BOT_TOKEN = settings.telegram_bot_token

# Create the bot and application
bot = Bot(token=TELEGRAM_BOT_TOKEN)
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

register_handlers(application)

async def send_message(chat_id: int, text: str) -> None:
    """Send a message to a Telegram chat."""
    await bot.send_message(chat_id=chat_id, text=text)

if __name__ == "__main__":
    import asyncio
    asyncio.run(application.run_polling()) 
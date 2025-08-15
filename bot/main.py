import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

from .database import init_db
from .handlers import start as h_start
from .handlers import commands as h_commands
from .handlers import process as h_process
from .handlers import admin as h_admin
from .utils.logger_util import setup_logger

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="instructions", description="تنظیم دستورالعمل ویراستاری"),
        BotCommand(command="openai", description="فقط از هوش مصنوعی OpenAI (Chat GPT) استفاده کن"),
        BotCommand(command="gemini", description="فقط از هوش مصنوعی گوگل (Gemini) استفاده کن"),
        BotCommand(command="help", description="توضیحات کار با بات"),
    ]
    await bot.set_my_commands(commands)

async def main():
    load_dotenv()
    logger = setup_logger()
    init_db()

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN not set")

    bot = Bot(
        token=token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())

    # Register routers instead of handlers
    dp.include_router(h_start.router)     # changed: these must now be routers
    dp.include_router(h_commands.router)
    dp.include_router(h_admin.router)
    h_process.set_logger(logger)
    dp.include_router(h_process.router)

    # Startup logic
    await bot.delete_webhook(drop_pending_updates=True)
    await set_commands(bot)
    logger.info("Starting workers...")
    await h_process.queue_manager.start()
    logger.info("Bot is up.")

    try:
        await dp.start_polling(bot)
    finally:
        logger.info("Stopping workers...")
        await h_process.queue_manager.stop()
        logger.info("Bye.")

if __name__ == "__main__":
    asyncio.run(main())

import os
from aiogram import Bot, Dispatcher, executor
from aiogram.types import BotCommand
from dotenv import load_dotenv

from .database import init_db
from .handlers import start as h_start
from .handlers import commands as h_commands
from .handlers import process as h_process
from .handlers import admin as h_admin
from .utils.logger_util import setup_logger
from aiogram.contrib.fsm_storage.memory import MemoryStorage

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="instructions", description="تنظیم دستورالعمل ویراستاری"),
        BotCommand(command="language", description="تنظیم زبان"),
        BotCommand(command="openai", description="فقط از هوش مصنوعی OpenAI (Chat GPT) استفاده کن"),
        BotCommand(command="gemini", description="فقط از هوش مصنوعی گوگل (Gemini) استفاده کن"),
        BotCommand(command="help", description="توضیحات کار با بات"),
        # می‌تونی دستورات دیگه هم اینجا اضافه کنی
    ]
    await bot.set_my_commands(commands)

def main():
    load_dotenv()
    logger = setup_logger()
    init_db()

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN not set")

    bot = Bot(token=token, parse_mode="HTML")
    dp = Dispatcher(bot, storage=MemoryStorage())  # <-- add storage

    h_start.register(dp, bot)
    h_commands.register(dp)
    h_admin.register(dp)
    h_process.set_logger(logger)
    h_process.register(dp, bot, logger)

    async def on_startup(_):
        logger.info("Starting workers...")
        await set_commands(bot)
        await h_process.queue_manager.start()
        logger.info("Bot is up.")

    async def on_shutdown(_):
        logger.info("Stopping workers...")
        await h_process.queue_manager.stop()
        logger.info("Bye.")

    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)

if __name__ == "__main__":
    main()


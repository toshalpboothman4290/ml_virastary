import io, time
from aiogram import types, Dispatcher
from ..database import get_user_by_tid, enqueue_job, update_job
from ..utils.settings_manager import get_rate_limit_seconds, get_max_words, get_default_provider
from ..utils.language_detect import detect_language
from ..utils.queue_manager import QueueManager, Job

rate_guard = {}  # telegram_id -> last_ts
queue_manager = QueueManager(workers=3)

def set_logger(logger):
    queue_manager.set_logger(logger)

def register(dp: Dispatcher, bot, logger):
    async def notify_queue_position(chat_id: int):
        pos = queue_manager.queue.qsize()
        await bot.send_message(chat_id, f"🧾 درخواست شما در صف قرار گرفت. جایگاه: {pos}")

    async def _process_text(message: types.Message, text: str):
        user = get_user_by_tid(message.from_user.id)

        # Rate limit
        now = time.time()
        rl = get_rate_limit_seconds()
        last = rate_guard.get(message.from_user.id, 0)
        if now - last < rl:
            wait = int(rl - (now - last))
            return await message.answer(f"⏳ بین دو درخواست حداقل {rl} ثانیه فاصله بگذارید. (باقی‌مانده: {wait}s)")
        rate_guard[message.from_user.id] = now

        # Validate text
        if not text or not text.strip():
            return await message.answer("⛔ متن خالی است.")
        if len(text.split()) > get_max_words():
            return await message.answer(f"⛔ متن طولانی است. حداکثر {get_max_words()} کلمه مجاز است.")

        # Language hint
        detected = detect_language(text)
        if user and user["preferred_language"] and user["preferred_language"] != detected:
            await message.answer(
                f"⚠️ زبان متن ({detected}) با تنظیم شما ({user['preferred_language']}) متفاوت است. "
                f"در صورت نیاز از /language استفاده کنید."
            )

        # Instruction + provider (per-user if set, otherwise default)
        instruction = (
            user["instructions"] if user and user["instructions"]
            else "اصلاح نگارشی و علائم، بدون تغییر محتوا یا لحن."
        )
        user_provider = (
            user["preferred_provider"]
            if user and ("preferred_provider" in user.keys()) and user["preferred_provider"]
            else None
        )
        provider = user_provider or get_default_provider()

        # Enqueue job
        job_id = enqueue_job(user["telegram_id"] if user else None, provider)
        job = Job(job_id, user, text, instruction, provider, dp.bot, message.chat.id, logger, update_job)
        await queue_manager.enqueue(job)
        await notify_queue_position(message.chat.id)

    # راهنما
    @dp.message_handler(commands=["send_text"])
    async def send_text_cmd(message: types.Message):
        await message.answer("متن یا فایل .txt را ارسال کنید.")

    # فقط فایل‌های .txt
    @dp.message_handler(content_types=types.ContentTypes.DOCUMENT)
    async def handle_doc(message: types.Message):
        if not message.document.file_name.endswith(".txt"):
            return await message.answer("⛔ فقط فایل .txt قبول است.")
        buffer = io.BytesIO()
        await message.document.download(destination=buffer)
        buffer.seek(0)
        text = buffer.read().decode("utf-8", errors="ignore")
        await _process_text(message, text)

    # فقط متن‌های عادی (نه دستورهای /...)
    @dp.message_handler(lambda m: m.content_type == "text" and m.text and not m.text.startswith("/"))
    async def handle_plain_text(message: types.Message):
        await _process_text(message, message.text)
import io, time
from aiogram import types, Dispatcher
from ..database import get_user_by_tid, enqueue_job, update_job
from ..utils.settings_manager import get_rate_limit_seconds, get_max_words, get_default_provider
from ..utils.language_detect import detect_language
from ..utils.queue_manager import QueueManager, Job

rate_guard = {}  # telegram_id -> last_ts
queue_manager = QueueManager(workers=3)

def set_logger(logger):
    queue_manager.set_logger(logger)

def register(dp: Dispatcher, bot, logger):
    async def notify_queue_position(chat_id: int):
        pos = queue_manager.queue.qsize()
        await bot.send_message(chat_id, f"🧾 درخواست شما در صف قرار گرفت. جایگاه: {pos}")

    async def _process_text(message: types.Message, text: str):
        user = get_user_by_tid(message.from_user.id)

        # Rate limit
        now = time.time()
        rl = get_rate_limit_seconds()
        last = rate_guard.get(message.from_user.id, 0)
        if now - last < rl:
            wait = int(rl - (now - last))
            return await message.answer(f"⏳ بین دو درخواست حداقل {rl} ثانیه فاصله بگذارید. (باقی‌مانده: {wait}s)")
        rate_guard[message.from_user.id] = now

        # Validate text
        if not text or not text.strip():
            return await message.answer("⛔ متن خالی است.")
        if len(text.split()) > get_max_words():
            return await message.answer(f"⛔ متن طولانی است. حداکثر {get_max_words()} کلمه مجاز است.")

        # Language hint
        detected = detect_language(text)
        if user and user["preferred_language"] and user["preferred_language"] != detected:
            await message.answer(
                f"⚠️ زبان متن ({detected}) با تنظیم شما ({user['preferred_language']}) متفاوت است. "
                f"در صورت نیاز از /language استفاده کنید."
            )

        # Instruction + provider (per-user if set, otherwise default)
        instruction = (
            user["instructions"] if user and user["instructions"]
            else "اصلاح نگارشی و علائم، بدون تغییر محتوا یا لحن."
        )
        user_provider = (
            user["preferred_provider"]
            if user and ("preferred_provider" in user.keys()) and user["preferred_provider"]
            else None
        )
        provider = user_provider or get_default_provider()

        # Enqueue job
        job_id = enqueue_job(user["telegram_id"] if user else None, provider)
        job = Job(job_id, user, text, instruction, provider, dp.bot, message.chat.id, logger, update_job)
        await queue_manager.enqueue(job)
        await notify_queue_position(message.chat.id)

    # راهنما
    @dp.message_handler(commands=["send_text"])
    async def send_text_cmd(message: types.Message):
        await message.answer("متن یا فایل .txt را ارسال کنید.")

    # فقط فایل‌های .txt
    @dp.message_handler(content_types=types.ContentTypes.DOCUMENT)
    async def handle_doc(message: types.Message):
        if not message.document.file_name.endswith(".txt"):
            return await message.answer("⛔ فقط فایل .txt قبول است.")
        buffer = io.BytesIO()
        await message.document.download(destination=buffer)
        buffer.seek(0)
        text = buffer.read().decode("utf-8", errors="ignore")
        await _process_text(message, text)

    # فقط متن‌های عادی (نه دستورهای /...)
    @dp.message_handler(lambda m: m.content_type == "text" and m.text and not m.text.startswith("/"))
    async def handle_plain_text(message: types.Message):
        await _process_text(message, message.text)

import io, time
from aiogram import Router, F
from aiogram.types import Message, ContentType
from ..database import get_user_by_tid, enqueue_job, update_job
from ..utils.settings_manager import get_rate_limit_seconds, get_max_words, get_default_provider
from ..utils.language_detect import detect_language
from ..utils.queue_manager import QueueManager, Job

router = Router()
rate_guard = {}
queue_manager = QueueManager(workers=3)

def set_logger(logger):
    queue_manager.set_logger(logger)

async def notify_queue_position(bot, chat_id: int):
    pos = queue_manager.queue.qsize()
    await bot.send_message(chat_id, f"🧾 درخواست شما در صف قرار گرفت. جایگاه: {pos}")

async def _process_text(bot, message: Message, text: str, logger):
    user = get_user_by_tid(message.from_user.id)

    # Rate limit
    now = time.time()
    rl = get_rate_limit_seconds()
    last = rate_guard.get(message.from_user.id, 0)
    if now - last < rl:
        wait = int(rl - (now - last))
        return await message.answer(f"⏳ بین دو درخواست حداقل {rl} ثانیه فاصله بگذارید. (باقی‌مانده: {wait}s)")
    rate_guard[message.from_user.id] = now

    # Validate
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

    instruction = (
        user["instructions"] if user and user["instructions"]
        else "اصلاح نگارشی و علائم، بدون تغییر محتوا یا لحن."
    )
    user_provider = (
        user["preferred_provider"]
        if user and "preferred_provider" in user and user["preferred_provider"]
        else None
    )
    provider = user_provider or get_default_provider()

    job_id = enqueue_job(user["telegram_id"] if user else None, provider)
    job = Job(job_id, user, text, instruction, provider, bot, message.chat.id, logger, update_job)
    await queue_manager.enqueue(job)
    await notify_queue_position(bot, message.chat.id)

# راهنما
@router.message(F.text == "/send_text")
async def send_text_cmd(message: Message):
    await message.answer("متن یا فایل .txt را ارسال کنید.")

# فقط فایل‌های .txt
@router.message(F.document.file_name.endswith(".txt"))
async def handle_doc(message: Message):
    buffer = io.BytesIO()
    await message.bot.download(
        message.document.file_id,
        destination=buffer
    )
    buffer.seek(0)
    text = buffer.read().decode("utf-8", errors="ignore")
    await _process_text(message.bot, message, text, queue_manager.logger)

# فقط متن‌های معمولی
@router.message(F.content_type == ContentType.TEXT, ~F.text.startswith("/"))
async def handle_plain_text(message: Message):
    await _process_text(message.bot, message, message.text, queue_manager.logger)

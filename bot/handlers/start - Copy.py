import os
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from bot.utils.upload_to_supabase_s3 import upload_file_to_s3
from ..database import upsert_user
from ..utils.settings_manager import (
    get_max_words,
    get_rate_limit_seconds,
    get_allowed_languages,
)

router = Router()

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROFILE_PICS_PATH = os.path.join(ROOT_DIR, "static/profile_pics")

@router.message(Command(commands=["start", "help"]))
async def start(message: Message):
    try:
        photos = await message.bot.get_user_profile_photos(message.from_user.id)
        if photos.total_count > 0:
            file = await message.bot.get_file(photos.photos[0][-1].file_id)
            os.makedirs(PROFILE_PICS_PATH, exist_ok=True)
            local_path = f"{PROFILE_PICS_PATH}/{message.from_user.id}.jpg"
            remote_key = f"profile_pics/{message.from_user.id}.jpg"

            await message.bot.download_file(file.file_path, local_path)
            upload_file_to_s3(local_path, remote_key)
            os.remove(local_path)
    except Exception as e:
        print(f"⚠️ Failed to fetch profile picture: {e}")

    upsert_user(
        message.from_user.id,
        message.from_user.full_name,
        message.from_user.username or "",
        f"{message.from_user.id}.jpg"
    )

    langs = "همه زبانها"
    max_words = get_max_words()
    rate = get_rate_limit_seconds()

    await message.answer(f"""
<b>✍️ بات ویراستار</b>

📝 ویرایش متن‌های شما با دقت و کیفیت بالا
🌍 ترجمه به همه زبان‌ها
⏱️ در کوتاه‌ترین زمان

💡 متن‌هات رو با این بات رایگان و بی‌شرط، جذاب‌تر و تاثیرگذارتر کن!

🔹 برای تغییر حالت (ویرایش، ترجمه و …)
از منو instructions رو انتخاب کن و دستور بده.
مثال: «این متن را از فارسی به انگلیسی ترجمه کن» 🌐

""".strip())

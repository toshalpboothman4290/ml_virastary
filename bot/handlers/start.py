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

    langs = ", ".join(get_allowed_languages())
    max_words = get_max_words()
    rate = get_rate_limit_seconds()

    await message.answer(f"""
<b>👋 سلام! به بات ویراستار هوشمند خوش آمدی</b>

من متن تو را با حفظ لحن و معنا ویراستاری می‌کنم (غلط‌گیری املایی، علائم، فاصله‌گذاری و روان‌سازی).

<b>🌐 زبان‌های پشتیبانی‌شده:</b> {langs}

<b>چطور شروع کنم؟</b>
• متن‌ات را همینجا ارسال کن؛ یا فایل <code>.txt</code> با کدینگ UTF-8 بفرست.  
• نتیجهٔ ویراستاری‌شده را همینجا دریافت می‌کنی.
<b>📝 دستورالعمل سفارشی</b>
• دستورالعمل پیشفرض این است:
غلط‌های املایی و تایپی رو درست کن
علائم نگارشی (، ؛ . ؟ !) رو سر جاش بذار
فاصله‌گذاری رو اصلاح کن
لحن نویسنده و معنی جملات رو تغییر نده
--------------
•اگر بخواهید دستورالعمل را تغییر دهید به شکل زیر اقدام کنید:
دستور <code>/instructions</code> را بزن؛ پیام بعدی‌ات به‌عنوان دستورالعمل ذخیره می‌شود. 
(مثال: «فقط علائم و غلط‌های املایی تصحیح شود. مطلقا ساختار جمله تغییر نکند»)

<b>🌍 تغییر زبان خروجی</b>
با <code>/language</code> یکی از زبان‌های بالا را انتخاب کن (مثلاً fa یا en).

<b>⚙️ موتور پردازش:</b> شما می‌توانید با دو موتور <b>OpenAI</b> و <b>Gemini</b> کار کنید. پیش‌فرض <b>OpenAI</b> است.  
<b>شیوه تعویض موتور:</b> با دستور <code>/OpenAi</code> یا <code>/Gemini</code> می‌توانید موتور را تغییر دهید.

<b>⏱ محدودیت‌ها</b>
• حداکثر طول متن: <b>{max_words}</b> کلمه  
• فاصلهٔ بین دو درخواست: <b>{rate}</b> ثانیه

✅ حالا متن یا فایل‌ات را بفرست تا شروع کنیم.
""".strip())

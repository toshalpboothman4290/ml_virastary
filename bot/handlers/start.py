# start.py
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


def _langs_str():
    try:
        langs = get_allowed_languages()
        if isinstance(langs, (list, tuple, set)):
            langs = "، ".join(map(str, langs))
        elif not isinstance(langs, str):
            langs = "همه زبان‌ها"
        return langs if langs.strip() else "همه زبان‌ها"
    except Exception:
        return "همه زبان‌ها"


@router.message(Command("start"))
async def cmd_start(message: Message):
    # دریافت و آپلود عکس پروفایل (اختیاری)
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

    # ثبت/به‌روزرسانی کاربر
    upsert_user(
        message.from_user.id,
        message.from_user.full_name,
        message.from_user.username or "",
        f"{message.from_user.id}.jpg",
    )

    # پیام خوش‌آمد (متن فعلیِ خودت حفظ شده)
    await message.answer(
        (
            "<b>✍️ بات ویراستار</b>\n\n"
            "📝 ویرایش متن‌های شما با دقت و کیفیت بالا\n"
            "🌍 ترجمه به همه زبان‌ها\n"
            "⏱️ در کوتاه‌ترین زمان\n\n"
            "💡 متن‌هات رو با این بات رایگان و بی‌شرط، جذاب‌تر و تاثیرگذارتر کن!\n\n"
            "🔹 برای تغییر حالت (ویرایش، ترجمه و …)\n"
            "از منو instructions رو انتخاب کن و دستور بده.\n"
            "مثال: «این متن را از فارسی به انگلیسی ترجمه کن» 🌐\n"
        ).strip(),
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    langs = _langs_str()
    try:
        max_words = get_max_words()
    except Exception:
        max_words = "—"
    try:
        rate = get_rate_limit_seconds()
    except Exception:
        rate = "—"

    help_text = f"""
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
• اگر بخواهید دستورالعمل را تغییر دهید به شکل زیر اقدام کنید:
دستور <code>/instructions</code> را بزن؛ پیام بعدی‌ات به‌عنوان دستورالعمل ذخیره می‌شود. 
(مثال: «فقط علائم و غلط‌های املایی تصحیح شود. مطلقا ساختار جمله تغییر نکند»)

<b>⚙️ موتور پردازش:</b> شما می‌توانید با دو موتور <b>OpenAI</b> و <b>Gemini</b> کار کنید. پیش‌فرض <b>OpenAI</b> است.  
<b>شیوه تعویض موتور:</b> با دستور <code>/OpenAi</code> یا <code>/Gemini</code> می‌توانید موتور را تغییر دهید.

<b>⏱ محدودیت‌ها</b>
• حداکثر طول متن: <b>{max_words}</b> کلمه  
• فاصلهٔ بین دو درخواست: <b>{rate}</b> ثانیه

✅ حالا متن یا فایل‌ات را بفرست تا شروع کنیم.
""".strip()

    await message.answer(help_text, parse_mode="HTML")

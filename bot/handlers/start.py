import os
from aiogram import types, Dispatcher
from bot.utils.upload_to_supabase_s3 import upload_file_to_s3
from ..database import upsert_user
from ..utils.settings_manager import (
    get_max_words,
    get_rate_limit_seconds,
    get_allowed_languages,
)

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROFILE_PICS_PATH = os.path.join(ROOT_DIR, "static/profile_pics")

def register(dp: Dispatcher, bot):
    @dp.message_handler(commands=["start", "help"])
    async def start(message: types.Message):
        # 🖼️ Try to fetch and save profile photo (optional)
        try:
            photos = await bot.get_user_profile_photos(message.from_user.id)
            if photos.total_count > 0:
                file = await bot.get_file(photos.photos[0][-1].file_id)
                local_folder  = PROFILE_PICS_PATH
                os.makedirs(local_folder, exist_ok=True)
                local_path = f"{local_folder}/{message.from_user.id}.jpg"
                remote_key = f"profile_pics/{message.from_user.id}.jpg"

                await bot.download_file(file_path=file.file_path, destination=local_path)

                upload_file_to_s3(local_path, remote_key)

                os.remove(local_path)  # optional: clean up
        except Exception as e:
            print(f"⚠️ Failed to fetch profile picture: {e}")

        # ثبت/به‌روزرسانی کاربر
        upsert_user(
            message.from_user.id,
            message.from_user.full_name,
            message.from_user.username or "",
            f"{message.from_user.id}.jpg"
        )

        # خواندن تنظیمات پویا
        langs = ", ".join(get_allowed_languages())
        max_words = get_max_words()
        rate = get_rate_limit_seconds()

        welcome = f"""
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

<b>📤 چگونه ارسال کنم؟</b>
<b>جهت ارسال متن:</b>  
• متن خود را مستقیم اینجا تایپ یا پیست کنید و ارسال کنید.
<b>جهت ارسال فایل:</b>  
• فایل <code>.txt</code> با کدینگ UTF-8 آماده کنید.  
• از منوی ارسال فایل تلگرام، گزینه <b>ارسال به صورت فایل</b> را انتخاب کنید (نه ارسال به صورت پیام متنی).  
• فایل را بفرستید تا پردازش شود.

✅ حالا متن یا فایل‌ات را بفرست تا شروع کنیم.
"""
        await message.answer(welcome.strip())

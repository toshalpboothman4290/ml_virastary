import os
from aiogram import types, Dispatcher
from ..database import get_setting, set_setting, stats_counts

def is_admin(user_id: int) -> bool:
    ids = (os.getenv("ADMIN_IDS") or "").split(",")
    ids = [x.strip() for x in ids if x.strip()]
    return str(user_id) in ids

def register(dp: Dispatcher):
    @dp.message_handler(commands=["settings"])
    async def settings_cmd(message: types.Message):
        if not is_admin(message.from_user.id):
            return await message.answer("⛔ دسترسی مجاز نیست.")
        info = [
            f"rate_limit_seconds = {get_setting('rate_limit_seconds', '30')}",
            f"max_words = {get_setting('max_words', '5000')}",
            f"allowed_languages = {get_setting('allowed_languages', 'fa,en,ar')}",
            f"default_provider = {get_setting('default_provider', 'openai')}",
        ]
        await message.answer("⚙️ تنظیمات:\n" + "\n".join(info))

    @dp.message_handler(commands=["set_setting"])
    async def set_setting_cmd(message: types.Message):
        if not is_admin(message.from_user.id):
            return await message.answer("⛔ دسترسی مجاز نیست.")
        try:
            _, key, *val = message.text.split()
            value = " ".join(val)
        except:
            return await message.answer("فرمت صحیح: /set_setting key value")
        if key not in {"rate_limit_seconds","max_words","allowed_languages","default_provider"}:
            return await message.answer("⛔ این کلید قابل تغییر از بات نیست.")
        set_setting(key, value)
        await message.answer(f"✅ تنظیم «{key}» روی «{value}» ذخیره شد.")

    @dp.message_handler(commands=["stats"])
    async def stats_cmd(message: types.Message):
        if not is_admin(message.from_user.id):
            return await message.answer("⛔ دسترسی مجاز نیست.")
        s = stats_counts()
        await message.answer("📊 آمار:\n" +
                             f"• کاربران: {s['users']}\n" +
                             f"• کل jobها: {s['jobs']} (pending: {s['pending']}, processing: {s['processing']}, done: {s['done']}, error: {s['error']})")

    @dp.message_handler(commands=["queue"])
    async def queue_cmd(message: types.Message):
        if not is_admin(message.from_user.id):
            return await message.answer("⛔ دسترسی مجاز نیست.")
        s = stats_counts()
        await message.answer(f"🧾 وضعیت صف (تقریبی بر اساس DB): pending = {s['pending']}, processing = {s['processing']}")

    @dp.message_handler(commands=["force_provider"])
    async def force_provider_cmd(message: types.Message):
        # if not is_admin(message.from_user.id):
        #     return await message.answer("⛔ دسترسی مجاز نیست.")
        parts = message.text.split()
        if len(parts) != 2 or parts[1] not in {"openai","gemini"}:
            return await message.answer("فرمت: /force_provider openai|gemini")
        set_setting("default_provider", parts[1])
        await message.answer(f"✅ موتور پیش‌فرض روی «{parts[1]}» تنظیم شد.")

    @dp.message_handler(commands=["reload_keys"])
    async def reload_keys_cmd(message: types.Message):
        if not is_admin(message.from_user.id):
            return await message.answer("⛔ دسترسی مجاز نیست.")
        from ..utils.key_manager import OPENAI_KEYS, GEMINI_KEYS
        OPENAI_KEYS.refresh(); GEMINI_KEYS.refresh()
        await message.answer(f"🔐 کلیدها — OpenAI: {OPENAI_KEYS.counts()} | Gemini: {GEMINI_KEYS.counts()}")

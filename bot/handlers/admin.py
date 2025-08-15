import os
from aiogram import Router
from aiogram.types import Message
from ..database import get_setting, set_setting, stats_counts
from ..utils.key_manager import OPENAI_KEYS, GEMINI_KEYS
from aiogram.filters import Command

router = Router()

def is_admin(user_id: int) -> bool:
    ids = (os.getenv("ADMIN_IDs") or "").split(",")
    ids = [x.strip() for x in ids if x.strip()]
    return str(user_id) in ids

@router.message(Command("settings"))
async def settings_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مجاز نیست.")
    info = [
        f"rate_limit_seconds = {get_setting('rate_limit_seconds', '30')}",
        f"max_words = {get_setting('max_words', '5000')}",
        f"allowed_languages = {get_setting('allowed_languages', 'fa,en,ar')}",
        f"default_provider = {get_setting('default_provider', 'openai')}",
    ]
    await message.answer("⚙️ تنظیمات:\n" + "\n".join(info))

@router.message(Command("set_setting"))
async def set_setting_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مجاز نیست.")
    try:
        _, key, *val = message.text.split()
        value = " ".join(val)
    except:
        return await message.answer("فرمت صحیح: /set_setting key value")
    if key not in {"rate_limit_seconds", "max_words", "allowed_languages", "default_provider"}:
        return await message.answer("⛔ این کلید قابل تغییر از بات نیست.")
    set_setting(key, value)
    await message.answer(f"✅ تنظیم «{key}» روی «{value}» ذخیره شد.")

@router.message(Command("stats"))
async def stats_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مجاز نیست.")
    s = stats_counts()
    await message.answer("📊 آمار:\n" +
                         f"• کاربران: {s['users']}\n" +
                         f"• کل jobها: {s['jobs']} (pending: {s['pending']}, processing: {s['processing']}, done: {s['done']}, error: {s['error']})")

@router.message(Command("queue"))
async def queue_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مجاز نیست.")
    s = stats_counts()
    await message.answer(f"🧾 وضعیت صف (تقریبی بر اساس DB): pending = {s['pending']}, processing = {s['processing']}")

@router.message(Command("force_provider"))
async def force_provider_cmd(message: Message):
    parts = message.text.split()
    if len(parts) != 2 or parts[1] not in {"openai", "gemini"}:
        return await message.answer("فرمت: /force_provider openai|gemini")
    set_setting("default_provider", parts[1])
    await message.answer(f"✅ موتور پیش‌فرض روی «{parts[1]}» تنظیم شد.")

@router.message(Command("reload_keys"))
async def reload_keys_cmd(message: Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ دسترسی مجاز نیست.")
    OPENAI_KEYS.refresh()
    GEMINI_KEYS.refresh()
    await message.answer(f"🔐 کلیدها — OpenAI: {OPENAI_KEYS.counts()} | Gemini: {GEMINI_KEYS.counts()}")

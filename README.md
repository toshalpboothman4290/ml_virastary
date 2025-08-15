# Virastary_Bot — نسخه صفر-دستکاری (Zero‑Touch)

فقط `.env` را پر کنید و اجرا کنید — بدون هیچ ویرایشی در کد.

**ویژگی‌ها**
- چندکلیدی برای OpenAI/Gemini (Round‑Robin + cooldown) + Failover بین موتورها
- SQLite با ساخت خودکار طبق `DB_URL` (پیش‌فرض: `sqlite:///data/users.db`)
- لاگ stdout (برای Render) + فایل با Rotation در `logs/bot.log`
- صف با ۳ ورکر + اعلام جایگاه صف
- دستورات ادمین: `/settings`, `/set_setting`, `/stats`, `/queue`, `/force_provider`, `/reload_keys`

## راه‌اندازی
1) Python 3.10+  
2) نصب: `pip install -r requirements.txt`  
3) ساخت `.env` از روی `.env.example` و پرکردن مقادیر  
4) اجرا: `python -m bot.main`

## نمونه `.env`
(همراه پکیج فایل `.env.example` هم هست)
```
BOT_TOKEN=...
OPENAI_API_KEYS=key1,key2
GEMINI_API_KEYS=keyA,keyB
DEFAULT_PROVIDER=openai
DB_TYPE=sqlite
DB_URL=sqlite:///data/users.db
ADMIN_IDs=100,200
RATE_LIMIT_SECONDS=30
MAX_WORDS=5000
ALLOWED_LANGUAGES=fa,en,ar,tr,de,fr
OPENAI_MODEL=gpt-4o-mini
GEMINI_MODEL=gemini-1.5-flash
```

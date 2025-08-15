import os
import logging
import google.generativeai as genai
from .key_manager import GEMINI_KEYS
from ..utils.notification import notify_admin

GEMINI_MODEL = os.getenv("GEMINI_MODEL","gemini-1.5-flash")

# خواندن آی‌دی ادمین‌ها از .env
# در .env باید چیزی مثل این باشه:
# ADMIN_IDs=7310546722,7321546722
ADMIN_IDs = {int(x) for x in os.getenv("ADMIN_IDs", "").split(",") if x.strip().isdigit()}

logger = logging.getLogger(__name__)
def _is_quota_error(msg: str) -> bool:
    if not msg: return False
    m = msg.lower()
    return ("quota" in m) or ("rate limit" in m) or ("resource exhausted" in m) or ("429" in m)

def process_with_gemini(instruction: str, text: str) -> str:
    tried = set()
    last_err = None
    total_keys = max(1, GEMINI_KEYS.counts())

    for idx in range(1, total_keys + 1):
        key = GEMINI_KEYS.next_key()
        if not key or key in tried:
            continue
        tried.add(key)

        log_msg = f"🔍 در حال بررسی کلید شماره {idx}"
        logger.info(log_msg)

        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(GEMINI_MODEL)
            prompt = (
                "شما یک ویراستار حرفه‌ای فارسی هستید. فقط ویراستاری کنید و محتوا/لحن را تغییر ندهید.\n\n"
                f"دستورالعمل ویراستاری:\n{instruction}\n\n---\n"
                f"متن ورودی:\n{text}\n\n"
                "لطفا خروجی نهایی ویراستاری‌شده را فقط برگردان."
            )
            resp = model.generate_content(prompt)
            out = resp.text or ""
            return out.strip()

        except Exception as e:
            msg = str(e)
            last_err = e
            if _is_quota_error(msg):
                warn_msg = f"❌ کلید شماره {idx} اعتبار ندارد. کلید بعدی را تست می‌کنم."
                logger.warning(warn_msg)
                GEMINI_KEYS.mark_cooldown(key, 600)
                continue
            raise

    final_msg = "🚫 هیچیک از کلیدهای جمنای معتبر نیستند."
    logger.error(final_msg)
    
    raise RuntimeError(final_msg)

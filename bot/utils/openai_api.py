import os
from openai import OpenAI
from .key_manager import OPENAI_KEYS

OPENAI_MODEL = os.getenv("OPENAI_MODEL","gpt-4o-mini")

def _is_quota_error(msg: str) -> bool:
    if not msg: return False
    m = msg.lower()
    return ("rate limit" in m) or ("quota" in m) or ("insufficient_quota" in m) or ("429" in m)

def process_with_openai(instruction: str, text: str) -> str:
    tried = set()
    last_err = None
    for _ in range(max(1, OPENAI_KEYS.counts())):
        key = OPENAI_KEYS.next_key()
        if not key or key in tried: continue
        tried.add(key)
        try:
            client = OpenAI(api_key=key)
            prompt = f"دستورالعمل ویراستاری:\n{instruction}\n\n---\nمتن ورودی:\n{text}\n\nخروجی نهایی ویراستاری‌شده:"
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role":"system","content":"شما یک ویراستار حرفه‌ای فارسی هستید. فقط ویراستاری کنید و محتوا/لحن را تغییر ندهید."},
                    {"role":"user","content":prompt}
                ],
                temperature=0.2
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            msg = str(e); last_err = e
            if _is_quota_error(msg):
                OPENAI_KEYS.mark_cooldown(key, 600)
                continue
            raise
    if last_err: raise last_err
    raise RuntimeError("No OPENAI_API_KEYS/OPENAI_API_KEY configured")

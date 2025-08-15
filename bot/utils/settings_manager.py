from ..database import get_setting

def get_rate_limit_seconds() -> int:
    val = get_setting("rate_limit_seconds","30")
    try: return int(val)
    except: return 30

def get_max_words() -> int:
    val = get_setting("max_words","5000")
    try: return int(val)
    except: return 5000

def get_allowed_languages():
    v = get_setting("allowed_languages","fa,en,ar")
    return [x.strip() for x in v.split(",") if x.strip()]

def get_default_provider():
    return get_setting("default_provider","openai")

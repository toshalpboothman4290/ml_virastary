import os, time

def _parse_multi(primary: str, single: str):
    raw = os.getenv(primary, "") or ""
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    if not keys:
        s = os.getenv(single, "").strip()
        if s: keys = [s]
    return keys

class RoundRobinKeys:
    def __init__(self, primary_env: str, single_env: str):
        self.primary_env = primary_env
        self.single_env = single_env
        self.keys = _parse_multi(primary_env, single_env)
        self.index = 0
        self.cooldown_until = {k: 0 for k in self.keys}

    def refresh(self):
        nk = _parse_multi(self.primary_env, self.single_env)
        if nk != self.keys:
            self.keys = nk
            self.index = 0
            self.cooldown_until = {k: 0 for k in self.keys}
        else:
            for k in self.keys:
                self.cooldown_until.setdefault(k, 0)

    def mark_cooldown(self, key: str, sec: int = 600):
        self.cooldown_until[key] = time.time() + sec

    def next_key(self) -> str:
        self.refresh()
        if not self.keys:
            return ""
        n = len(self.keys)
        for _ in range(n):
            k = self.keys[self.index % n]
            self.index += 1
            if time.time() >= self.cooldown_until.get(k, 0):
                return k
        return self.keys[self.index % n]

    def counts(self):
        self.refresh()
        return len(self.keys)

OPENAI_KEYS = RoundRobinKeys("OPENAI_API_KEYS","OPENAI_API_KEY")
GEMINI_KEYS = RoundRobinKeys("GEMINI_API_KEYS","GEMINI_API_KEY")

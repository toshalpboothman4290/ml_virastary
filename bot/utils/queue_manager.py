from .openai_api import process_with_openai
from .gemini_api import process_with_gemini

class Job:
    def __init__(self, job_id: int, user, text: str, instruction: str,
                 first_provider: str, bot, chat_id: int, logger, db_update_job):
        self.job_id = job_id
        self.user = user
        self.text = text
        self.instruction = instruction
        self.first_provider = first_provider
        self.bot = bot
        self.chat_id = chat_id
        self.logger = logger
        self.db_update_job = db_update_job

class QueueManager:
    def __init__(self, workers: int = 3):
        import asyncio
        self.queue = asyncio.Queue()
        self.workers = workers
        self._workers = []
        self.logger = None

    def set_logger(self, logger):
        self.logger = logger

    async def start(self):
        import asyncio
        for _ in range(self.workers):
            self._workers.append(asyncio.create_task(self.worker()))

    async def stop(self):
        for _ in self._workers:
            await self.queue.put(None)
        import asyncio
        await asyncio.gather(*self._workers)

    async def enqueue(self, job: Job):
        await self.queue.put(job)

    async def worker(self):
        while True:
            job = await self.queue.get()
            if job is None:
                break
            await self.process(job)
            self.queue.task_done()

    # ---------------- core logic: send edited text, smart failover ----------------
    async def process(self, job: Job):
        def _is_quota_like(msg: str) -> bool:
            if not msg:
                return False
            m = msg.lower()
            return ("rate limit" in m) or ("quota" in m) or ("insufficient_quota" in m) or ("429" in m) or ("resource exhausted" in m)

        def _run(provider: str) -> str:
            if provider == "openai":
                return process_with_openai(job.instruction, job.text)
            else:
                return process_with_gemini(job.instruction, job.text)

        # mark processing in DB
        try:
            job.db_update_job(job.job_id, status="processing")
        except Exception:
            pass

        primary = job.first_provider
        fallback = "gemini" if primary == "openai" else "openai"

        # try primary
        try:
            if self.logger: self.logger.info(f"Processing job {job.job_id} with {primary}")
            out = _run(primary) or ""
            # تلگرام حداکثر 4096 کاراکتر پیام؛ ما کمی کمتر می‌فرستیم
            await job.bot.send_message(job.chat_id, out[:4000] if out.strip() else "✅ پردازش انجام شد.")
            job.db_update_job(job.job_id, status="done", provider=primary, retry_count=0)
            return
        except Exception as e1:
            msg1 = str(e1)
            if self.logger: self.logger.error(f"Job {job.job_id} failed on {primary}: {msg1}")

            # فقط وقتی شبیه خطای سهمیه است، به موتور دوم سوئیچ کن
            if not _is_quota_like(msg1):
                await job.bot.send_message(job.chat_id, f"❌ پردازش با موتور «{primary}» انجام نشد — {msg1[:300]}")
                job.db_update_job(job.job_id, status="error", error_message=msg1)
                return

            # try fallback
            try:
                if self.logger: self.logger.info(f"Failover job {job.job_id} to {fallback}")
                out = _run(fallback) or ""
                note = f"\n\nℹ️ به‌دلیل محدودیت در موتور {primary}، با {fallback} انجام شد."
                await job.bot.send_message(job.chat_id, (out[:4000] + note) if out.strip() else ("✅ پردازش انجام شد." + note))
                job.db_update_job(job.job_id, status="done", provider=fallback, retry_count=1)
                return
            except Exception as e2:
                msg2 = str(e2)
                if self.logger: self.logger.error(f"Job {job.job_id} failed on fallback {fallback}: {msg2}")
                await job.bot.send_message(job.chat_id, f"❌ پردازش انجام نشد — {msg2[:300]}")
                job.db_update_job(job.job_id, status="error", error_message=msg2)

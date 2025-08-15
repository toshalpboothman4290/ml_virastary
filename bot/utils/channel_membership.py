from aiogram.enums import ChatMemberStatus
from aiogram.types import Message
from dotenv import load_dotenv
import os

load_dotenv()
CHANNEL_USERNAME = "@majaleh20_30"  # Replace with your actual channel
ADMIN_IDs = os.getenv("ADMIN_IDs")
ADMINS = [int(item.strip()) for item in ADMIN_IDs.split(",") if item.strip()]

async def is_user_member(user_id: int, bot) -> bool:
    if user_id in ADMINS:
        return True

    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in {
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR
        }
    except Exception as e:
        print(f"[ERROR] get_chat_member failed: {e}")
        return False
    
async def display_membership_banner(message: Message):
    join_link = f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"
    await message.answer(
        f"🚫 لطفا در کانال ما عضو شوید تا بتوانید از امکانات دانلود بات استفاده کنید.\n\n"
        f"👉 [برای عضو شدن کلیک کنید]({join_link})\n\n"
        f"بعد از عضو شدن لطفا دوباره بزنید /start",
        parse_mode="Markdown"
    )
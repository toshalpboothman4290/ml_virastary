from dotenv import load_dotenv
import os

load_dotenv()
ADMIN_IDs = os.getenv("ADMIN_IDs")
ADMINS = [int(item.strip()) for item in ADMIN_IDs.split(",") if item.strip()]
    
async def notify_admin(bot, text: str):
    for admin in ADMINS:
        try:
            await bot.send_message(chat_id=admin, text=text)
        except Exception as e:
            print(f"❌ ERROR sending message to admin {admin}: {e}")
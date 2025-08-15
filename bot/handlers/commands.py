from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from ..database import set_user_instruction, set_user_language, set_user_provider
from ..utils.settings_manager import get_allowed_languages

class Form(StatesGroup):
    waiting_instruction = State()
    waiting_language = State()

def register(dp: Dispatcher):
    # --- دستورالعمل سفارشی کاربر ---
    @dp.message_handler(commands=["instructions"])
    async def instructions_cmd(message: types.Message, state: FSMContext):
        await message.answer("✍️ دستورالعمل ویراستاری را بفرستید. پیام بعدی شما ذخیره می‌شود.")
        await Form.waiting_instruction.set()

    @dp.message_handler(state=Form.waiting_instruction, content_types=types.ContentTypes.TEXT)
    async def save_instruction(message: types.Message, state: FSMContext):
        set_user_instruction(message.from_user.id, message.text.strip())
        await message.answer("✅ دستورالعمل ذخیره شد.")
        await state.finish()

    # --- تغییر زبان خروجی ---
    @dp.message_handler(commands=["language"])
    async def language_cmd(message: types.Message, state: FSMContext):
        langs = get_allowed_languages()
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for l in langs:
            kb.add(types.KeyboardButton(l))
        await message.answer("یک زبان انتخاب کن:", reply_markup=kb)
        await Form.waiting_language.set()

    @dp.message_handler(state=Form.waiting_language, content_types=types.ContentTypes.TEXT)
    async def save_language(message: types.Message, state: FSMContext):
        lang = message.text.strip()
        if lang not in get_allowed_languages():
            await message.answer("⛔ زبان نامعتبر است. از دکمه‌ها انتخاب کن.")
            return
        set_user_language(message.from_user.id, lang)
        await message.answer(f"✅ زبان شما روی «{lang}» تنظیم شد.", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()

    # --- تعویض موتور ---
    @dp.message_handler(commands=["openai", "OpenAi"])
    async def set_openai(message: types.Message):
        set_user_provider(message.from_user.id, "openai")
        await message.answer("✅ موتور پردازش شما روی «OpenAI» تنظیم شد. (فقط برای حساب شما)")

    @dp.message_handler(commands=["gemini", "Gemini"])
    async def set_gemini(message: types.Message):
        set_user_provider(message.from_user.id, "gemini")
        await message.answer("✅ موتور پردازش شما روی «Gemini» تنظیم شد. (فقط برای حساب شما)")

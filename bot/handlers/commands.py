from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from ..database import set_user_instruction, set_user_language, set_user_provider
from ..utils.settings_manager import get_allowed_languages
from aiogram.filters import Command

router = Router()

class Form(StatesGroup):
    waiting_instruction = State()
    waiting_language = State()

# --- دستورالعمل سفارشی کاربر ---
@router.message(Command("instructions"))
async def instructions_cmd(message: Message, state: FSMContext):
    await message.answer("✍️ دستورالعمل ویراستاری را بفرستید. پیام بعدی شما ذخیره می‌شود.")
    await state.set_state(Form.waiting_instruction)

@router.message(Form.waiting_instruction, F.text)
async def save_instruction(message: Message, state: FSMContext):
    set_user_instruction(message.from_user.id, message.text.strip())
    await message.answer("✅ دستورالعمل ذخیره شد.")
    await state.clear()

# --- تغییر زبان خروجی ---
@router.message(Command("language"))
async def language_cmd(message: Message, state: FSMContext):
    langs = get_allowed_languages()
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=l)] for l in langs],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer("یک زبان انتخاب کن:", reply_markup=kb)
    await state.set_state(Form.waiting_language)

@router.message(Form.waiting_language, F.text)
async def save_language(message: Message, state: FSMContext):
    lang = message.text.strip()
    if lang not in get_allowed_languages():
        await message.answer("⛔ زبان نامعتبر است. از دکمه‌ها انتخاب کن.")
        return
    set_user_language(message.from_user.id, lang)
    await message.answer(f"✅ زبان شما روی «{lang}» تنظیم شد.", reply_markup=ReplyKeyboardRemove())
    await state.clear()

# --- تعویض موتور ---

@router.message(Command("openai"))
async def set_openai(message: Message):
    set_user_provider(message.from_user.id, "openai")
    await message.answer("✅ موتور پردازش شما روی «OpenAI» تنظیم شد. (فقط برای حساب شما)")

@router.message(Command("gemini"))
async def set_gemini(message: Message):
    set_user_provider(message.from_user.id, "gemini")
    await message.answer("✅ موتور پردازش شما روی «Gemini» تنظیم شد. (فقط برای حساب شما)")

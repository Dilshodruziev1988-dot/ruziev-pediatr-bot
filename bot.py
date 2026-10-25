import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = {
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}
CHANNEL_ID = os.getenv("CHANNEL_ID", "").strip()

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Add it in your hosting environment variables.")

bot = Bot(TOKEN)
dp = Dispatcher()

TEXTS = {
    "uz": {
        "welcome": (
            "👨‍⚕️ Assalomu alaykum! Men doktor Ruziyevning rasmiy yordamchi botiman.\n\n"
            "Bu yerda bolalar salomatligi, parvarishi va ovqatlanishi haqida foydali "
            "ma’lumotlar hamda yangi postlar havolalarini topasiz.\n\n"
            "⚠️ Botdagi ma’lumotlar shifokor ko‘rigini almashtirmaydi. Bola og‘ir ahvolda "
            "bo‘lsa, zudlik bilan tibbiy yordamga murojaat qiling."
        ),
        "menu": "Kerakli bo‘limni tanlang:",
        "channel": "📢 Telegram kanal",
        "instagram": "📸 Instagram sahifalari",
        "posts": "🩺 Foydali tavsiyalar",
        "language": "🌐 Tilni tanlash",
        "contact": "📩 Aloqa",
        "about": "👨‍⚕️ Doktor Ruziyev Dilshod Ramazonovich — pediatr.\nBolalar salomatligi haqida foydali ma’lumotlar va ota-onalar uchun tavsiyalar.",
        "choose_lang": "Tilni tanlang / Выберите язык:",
        "saved": "Til saqlandi: O‘zbekcha 🇺🇿",
        "help": "Buyruqlar:\n/start — boshlash\n/language — tilni tanlash\n/help — yordam",
        "admin_only": "Bu buyruq faqat bot administratori uchun.",
        "post_usage": "Foydalanish: /post uz Matn yoki /post ru Текст\nBot kanalga post yuborishi uchun kanal administratori bo‘lishi kerak.",
        "posted": "Post kanalga yuborildi.",
        "post_error": "Post yuborilmadi. CHANNEL_ID va botning kanal admin huquqlarini tekshiring."
    },
    "ru": {
        "welcome": (
            "👨‍⚕️ Здравствуйте! Я официальный бот-помощник доктора Рузиева.\n\n"
            "Здесь вы найдёте полезные материалы о здоровье, уходе и питании детей, "
            "а также ссылки на новые публикации.\n\n"
            "⚠️ Информация бота не заменяет осмотр врача. При тяжёлом состоянии ребёнка "
            "срочно обратитесь за медицинской помощью."
        ),
        "menu": "Выберите нужный раздел:",
        "channel": "📢 Telegram-канал",
        "instagram": "📸 Instagram",
        "posts": "🩺 Полезные рекомендации",
        "language": "🌐 Выбрать язык",
        "contact": "📩 Контакты",
        "about": "👨‍⚕️ Доктор Рузиев Дилшод Рамазонович — педиатр.\nПолезная информация о здоровье детей и рекомендации для родителей.",
        "choose_lang": "Выберите язык / Tilni tanlang:",
        "saved": "Язык сохранён: Русский 🇷🇺",
        "help": "Команды:\n/start — начать\n/language — выбрать язык\n/help — помощь",
        "admin_only": "Эта команда доступна только администратору бота.",
        "post_usage": "Использование: /post uz Текст или /post ru Текст\nДля публикации бот должен быть администратором канала.",
        "posted": "Пост опубликован в канале.",
        "post_error": "Не удалось опубликовать пост. Проверьте CHANNEL_ID и права администратора бота."
    }
}

# In-memory language choice; users can reselect it any time.
# For persistence across restarts, connect a database later.
user_languages = {}

def get_lang(user_id: int) -> str:
    return user_languages.get(user_id, "uz")

def language_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="O‘zbekcha 🇺🇿", callback_data="lang:uz"),
        InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang:ru"),
    ]])

def main_keyboard(lang: str):
    t = TEXTS[lang]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t["channel"], url="https://t.me/rpediatrruziyev")],
        [
            InlineKeyboardButton(text="@dr_ruziev_pediatr", url="https://www.instagram.com/dr_ruziev_pediatr/"),
            InlineKeyboardButton(text="@ruziev_pediatr", url="https://www.instagram.com/ruziev_pediatr/"),
        ],
        [InlineKeyboardButton(text=t["posts"], callback_data="section:posts")],
        [InlineKeyboardButton(text=t["contact"], callback_data="section:contact"),
         InlineKeyboardButton(text=t["language"], callback_data="section:language")],
    ])

@dp.message(CommandStart())
async def start(message: Message):
    lang = get_lang(message.from_user.id)
    await message.answer(TEXTS[lang]["welcome"], reply_markup=main_keyboard(lang))

@dp.message(Command("help"))
async def help_command(message: Message):
    await message.answer(TEXTS[get_lang(message.from_user.id)]["help"])

@dp.message(Command("language"))
async def language_command(message: Message):
    await message.answer(TEXTS[get_lang(message.from_user.id)]["choose_lang"], reply_markup=language_keyboard())

@dp.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery):
    lang = callback.data.split(":", 1)[1]
    user_languages[callback.from_user.id] = lang
    await callback.answer()
    await callback.message.edit_text(TEXTS[lang]["welcome"], reply_markup=main_keyboard(lang))

@dp.callback_query(F.data == "section:language")
async def language_section(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(TEXTS[get_lang(callback.from_user.id)]["choose_lang"], reply_markup=language_keyboard())

@dp.callback_query(F.data == "section:posts")
async def posts_section(callback: CallbackQuery):
    lang = get_lang(callback.from_user.id)
    if lang == "uz":
        msg = "🩺 Foydali postlar va yangi videolar uchun Telegram kanalimizni kuzatib boring."
    else:
        msg = "🩺 Следите за Telegram-каналом, чтобы не пропускать полезные публикации и новые видео."
    await callback.answer()
    await callback.message.answer(msg, reply_markup=main_keyboard(lang))

@dp.callback_query(F.data == "section:contact")
async def contact_section(callback: CallbackQuery):
    lang = get_lang(callback.from_user.id)
    msg = ("📩 Kanal orqali bog‘laning: @rpediatrruziyev" if lang == "uz"
           else "📩 Свяжитесь через канал: @rpediatrruziyev")
    await callback.answer()
    await callback.message.answer(msg, reply_markup=main_keyboard(lang))

@dp.message(Command("post"))
async def admin_post(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(TEXTS[get_lang(message.from_user.id)]["admin_only"])
        return
    if not CHANNEL_ID:
        await message.answer("CHANNEL_ID не задан в переменных окружения.")
        return
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3 or parts[1] not in ("uz", "ru"):
        await message.answer(TEXTS[get_lang(message.from_user.id)]["post_usage"])
        return
    lang, content = parts[1], parts[2]
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=content)
        await message.answer(TEXTS[lang]["posted"])
    except Exception:
        logging.exception("Channel post failed")
        await message.answer(TEXTS[lang]["post_error"])

async def main():
    # Polling is a simple way to start. Keep only one running instance of this bot.
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

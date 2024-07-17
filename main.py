import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from deep_translator import GoogleTranslator
from gtts import gTTS
import os

from config import TOKEN

# Настройка логирования
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Создание папок для сохранения изображений и голосовых сообщений, если они не существуют
if not os.path.exists('img'):
    os.makedirs('img')

if not os.path.exists('vcm'):
    os.makedirs('vcm')

# Определение состояний для FSM
class Form(StatesGroup):
    waiting_for_text = State()
    waiting_for_translation = State()

# Обработчик команды /start
@dp.message(Command("start"))
async def send_welcome(message: Message):
    await message.reply("Привет! Отправь мне задание и я выполню его.")

# Обработчик команды /help
@dp.message(Command("help"))
async def send_help(message: Message):
    await message.reply("Этот бот умеет:\n\n"
                        "Сохранять отправленное ему фото - /photo\n"
                        "Отправлять голосовые сообщения по введенному тексту - /text\n"
                        "Переводить введенный текст на английский язык и отправлять в виде голосового сообщения - /translate\n")

# Обработчик команды /text
@dp.message(Command("text"))
async def request_text(message: Message, state: FSMContext):
    await message.reply("Пожалуйста, введите текст, который вы хотите преобразовать в голосовое сообщение.")
    await state.set_state(Form.waiting_for_text)

# Обработчик текста после команды /text
@dp.message(Form.waiting_for_text)
async def handle_text(message: Message, state: FSMContext):
    text = message.text
    tts = gTTS(text, lang='ru')
    file_path = f"vcm/{message.message_id}.ogg"
    tts.save(file_path)

    audio = FSInputFile(file_path)
    await bot.send_audio(message.chat.id, audio)
    os.remove(file_path)

    await state.clear()

# Обработчик команды /translate
@dp.message(Command("translate"))
async def request_translation_text(message: Message, state: FSMContext):
    await message.reply("Пожалуйста, введите текст, который вы хотите перевести на английский и преобразовать в голосовое сообщение.")
    await state.set_state(Form.waiting_for_translation)

# Обработчик текста после команды /translate
@dp.message(Form.waiting_for_translation)
async def handle_translation(message: Message, state: FSMContext):
    text_to_translate = message.text
    translator = GoogleTranslator(source='auto', target='en')
    translated_text = translator.translate(text_to_translate)

    tts = gTTS(translated_text, lang='en')
    file_path = f"vcm/{message.message_id}_translated.ogg"
    tts.save(file_path)

    audio = FSInputFile(file_path)
    await bot.send_audio(message.chat.id, audio)
    os.remove(file_path)

    await state.clear()

# Обработчик фото
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    photo = message.photo[-1]  # Получаем фото с наибольшим разрешением
    file_info = await bot.get_file(photo.file_id)
    file_path = file_info.file_path
    file_name = os.path.join('img', f"{photo.file_id}.jpg")

    await bot.download_file(file_path, file_name)
    await message.reply(f"Фото сохранено как {file_name}")


async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

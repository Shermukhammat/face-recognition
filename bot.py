import asyncio, os, sys
from config import TOKEN, ADMINS_ID
from aiogram import Bot, Dispatcher, html, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from data import DataBase, User


def resource_path(relative_path):
    """ Get absolute path to resource, works for development and PyInstaller EXE """
    if getattr(sys, 'frozen', False):  # If running as compiled EXE
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


dp = Dispatcher()
reply_markup = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
            [
                KeyboardButton(text = "➕  Foydalanuvchi qo'shish"),
                KeyboardButton(text = "➖  Foydalanuvchini o'chirish")
            ]
        ])
back_markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text = "⬅️  Orqaga")]])

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    if message.from_user.id in ADMINS_ID:
        await message.answer("Xush kelibsiz admin!", reply_markup=reply_markup)



@dp.message(lambda message: message.from_user.id in ADMINS_ID, F.content_type == "photo")
async def photo_handler(message: Message, bot: Bot, db: DataBase) -> None:
    if not message.caption:
        await message.reply("Rasmga ism familyani qo'shing", reply_markup=back_markup)
        return

    # Step 1: Add user to database with initial empty photo_path
    user = User(name=message.caption, photo_path="")
    user = db.add_user(user)  # Get the refreshed user with id

    # Step 2: Get file extension from Telegram
    file = await bot.get_file(message.photo[-1].file_id)
    file_extension = os.path.splitext(file.file_path)[1]  # Extracts e.g., '.jpg' or '.png'

    # Step 3: Download the photo with user.id and correct extension
    folder = "data/images"
    file_name = f"{user.id}{file_extension}"  # e.g., "1.jpg"
    destination = resource_path(f"{folder}/{file_name}")
  
    await bot.download(file.file_id, destination = destination)

    # Step 4: Update user with photo_path
    user.photo_path = destination
    db.update_user(user)

    await message.reply(f"✅ Foydalanuvchi {message.caption} qo'shildi, id raqami {user.id}", reply_markup=reply_markup)

@dp.message(lambda message: message.text.isnumeric() and message.from_user.id in ADMINS_ID)
async def delete_user(message: Message, db : DataBase) -> None:
    user = db.get_user(int(message.text))
    if not user:
        await message.reply("❌ Bunday foydalanuvchi topilmadi", reply_markup=reply_markup)
        return
    
    db.delete_user(int(message.text))
    os.remove(user.photo_path)
    await message.reply(f"✅ Foydalanuvchi {user.name} o'chirildi", reply_markup=reply_markup)

@dp.message(lambda message: message.from_user.id in ADMINS_ID)
async def main_handler(message: Message) -> None:
    if message.text == "➕  Foydalanuvchi qo'shish":
        await message.answer("Qo'shmoqchi bo'lgan foydalanuvchini rasmi bilan ismni yuboring", reply_markup=back_markup)
    
    elif message.text == "➖  Foydalanuvchini o'chirish":
        await message.answer("Foydalanuvchini id raqamini yuboring", reply_markup=back_markup)
    
    else:
        await message.answer("Bosh menyu", reply_markup=reply_markup)



async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    db = DataBase('data/data.sqlite')
    dp["db"] = db
    await dp.start_polling(bot)


if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
import asyncio, os, sys
from config import TOKEN, ADMINS_ID
from aiogram import Bot, Dispatcher, html, F, types
from aiogram.fsm.context import FSMContext 
from aiogram.fsm.state import State, StatesGroup 
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from data import DataBase, User, Group
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.storage.memory import MemoryStorage
import shutil
from asyncio import sleep

def resource_path(relative_path):
    """ Get absolute path to resource, works for development and PyInstaller EXE """
    if getattr(sys, 'frozen', False):  # If running as compiled EXE
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class AutoButtons:
    def __init__(self, width : int = 3):
        self.buttons = [[]]
        self.index = 0
        self.curent_item_count = 0
        self.width = width
    
    
    def add_button(self, button : InlineKeyboardButton, new_line : bool = False):
        if new_line:
            self.index += 1
            self.curent_item_count = 1
                
            self.buttons.append([])
            self.buttons[self.index].append(button)
            
        else:
            if self.curent_item_count < self.width:
                self.curent_item_count += 1
                self.buttons[self.index].append(button)
            else:
                self.index += 1
                self.curent_item_count = 1
                
                self.buttons.append([])
                self.buttons[self.index].append(button)
    
    def get_buttons(self):
        return self.buttons
    
    @property
    def inline_markup(self):
        if self.buttons:
            return InlineKeyboardMarkup(inline_keyboard=self.buttons)
    
    @property
    def keyboard_markup(self):
        if self.buttons:
            return ReplyKeyboardMarkup(keyboard=self.buttons, resize_keyboard=True)
        
    def reset(self):
        self.buttons = [[]]
        self.index = 0
        self.curent_item_count = 0


class MainState(StatesGroup):
    get_new_user = State()
    delete_user = State()
    add_group = State()
    delete_group = State()

dp = Dispatcher(storage=MemoryStorage())
reply_markup = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
            [KeyboardButton(text = "📋 Foydalanuvchilar"), KeyboardButton(text="📦 Jadvallar")],
            [
                KeyboardButton(text = "➕ Qo'shish"),
                KeyboardButton(text = "➖  O'chirish")
            ],
            [KeyboardButton(text="🗑 Guruh o'chirish")]
        ])
back_markup = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[[KeyboardButton(text = "⬅️  Orqaga")]])

def groups_markup(groups: list[str]) -> types.ReplyKeyboardMarkup:
    buttons = AutoButtons()
    for group in groups:
        buttons.add_button(KeyboardButton(text=group))
    
    buttons.add_button(KeyboardButton(text="⬅️ Orqaga"), new_line=True)
    return buttons.keyboard_markup

@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    if message.from_user.id in ADMINS_ID:
        await message.answer("Xush kelibsiz admin!", reply_markup=reply_markup)



@dp.message(F.photo, MainState.get_new_user)
async def photo_handler(message: Message, bot: Bot, db: DataBase, state: FSMContext) -> None:
    if not message.caption:
        await message.reply("❗️ Rasmga ism familyani qo'shing", reply_markup=back_markup)
        return

    elif len(message.caption) > 30:
        await message.reply("❗️ Foydalanuvchi ism familyasi 30ta belgidan ko'p bo'lishi mumkun emas", reply_markup=back_markup)
        return
    
    state_data = await state.get_data()
    await state.clear()
    group = state_data.get('group')
    user = User(name=message.caption, group=group, photo_path="")
    user = db.add_user(user)  

    file = await bot.get_file(message.photo[-1].file_id)
    file_extension = os.path.splitext(file.file_path)[1]

    folder = "data/images"
    file_name = f"{user.id}{file_extension}" 
    destination = f"{folder}/{file_name}"
  
    await bot.download(file.file_id, destination=resource_path(destination))

    user.photo_path = destination
    db.update_user(user)

    await message.reply(f"✅ Foydalanuvchi {message.caption} qo'shildi, id raqami {user.id}", reply_markup=reply_markup)


@dp.message(MainState.delete_user)
async def delete_user(message: Message, db : DataBase, state: FSMContext) -> None:
    if message.text == "⬅️  Orqaga":
        await state.clear()
        await message.answer("Bosh menyu", reply_markup=reply_markup)
        return

    if not message.text.isnumeric():
        await message.answer("Id ni faqat raqam ko'rnishda kiriting", reply_markup=back_markup)
        return

    user = db.get_user(int(message.text))
    if not user:
        await message.reply("❌ Bunday foydalanuvchi topilmadi", reply_markup=back_markup)
        return
    
    await state.clear()
    db.delete_user(int(message.text))
    os.remove(resource_path(user.photo_path))
    await message.reply(f"✅ Foydalanuvchi {user.name} o'chirildi", reply_markup=reply_markup)


@dp.callback_query(lambda query: query.data == 'add_group')
async def add_group_callback(query: types.CallbackQuery, state: FSMContext):
    await state.set_state(MainState.add_group)
    await query.message.answer("✍️ Yangi guruh nomini kirting", reply_markup=back_markup)


@dp.message(MainState.add_group)
async def get_group_name(update: types.Message, state: FSMContext, db: DataBase):
    if update.text == "⬅️  Orqaga":
        await state.clear()
        await update.answer("Bosh menyu", reply_markup=reply_markup)
    
    elif not update.text.replace('-', '').replace(' ', '').isalnum():
        await update.reply("❌ Guruh nomi faqat ingliz harflari va raqamlardan iborat bo'lishi kerak", reply_markup=back_markup)
    
    elif len(update.text) > 15:
        await update.reply("❌ Guruh nomi 15ta beligdan kop bo'lishi mumkun emas", reply_markup=back_markup)

    elif update.text in [group.name for group in db.groups]:
        await update.reply("❌ Bunday guruh mavjud", reply_markup=back_markup)
    
    else:
        Group(name=update.text.strip(), create=True)
        db.add_group(update.text.strip())
        await update.reply(f"✅ Yangi guruh {update.text.strip()} qo'shildi", reply_markup=reply_markup)
        await state.clear()

@dp.message(MainState.get_new_user)
async def get_new_user(update: types.Message, state: FSMContext, db: DataBase):
    if update.text == "⬅️  Orqaga":
        await state.clear()
        await update.answer("Bosh menyu", reply_markup=reply_markup)
    else:
        await update.reply("❌ Yangi foydalanuvchi rasmi bilan ism familyasni yuboring bitta xabarda", reply_markup=back_markup)

@dp.callback_query(lambda query: query.data.startswith("group_"))
async def start_adding_user(query: types.CallbackQuery, state: FSMContext, db: DataBase):
    group = query.data.replace('group_', '')
    if group in [group.name for group in db.groups]:
        await state.set_state(MainState.get_new_user)
        await state.update_data({'group': group})
        await query.message.answer("⬆️ Yangi foydalanuvchini rasmini ismi familyasi bilan yuboring", reply_markup=back_markup)
    else:
        await query.answer("❌ Bunday kurs mavjud emas", show_alert=True)


@dp.callback_query(lambda query: query.data.startswith("table_"))
async def start_adding_user(query: types.CallbackQuery, state: FSMContext, db: DataBase):
    group = query.data.replace('table_', '')
    if group in [group.name for group in db.groups]:
        for gr in db.groups:
            if gr.name == group:
                for path in gr.excels_path:
                    await query.message.answer_document(types.FSInputFile(path), caption = group)
                    await sleep(5)
    else:
        await query.answer("❌ Bunday kurs mavjud emas", show_alert=True)

@dp.message(MainState.delete_group)
async def delete_group(update: types.Message, state: FSMContext, db: DataBase):
    state_data = await state.get_data()
    if update.text == "⬅️ Orqaga":
        await state.clear()
        await update.answer("Bosh menyu", reply_markup=reply_markup)
        
    elif update.text in [group.name for group in db.groups]:
        confirmed_group = state_data.get('confirmed_group')
        if update.text == confirmed_group:
            users = db.get_group_users(update.text)
            for user in users:
                os.remove(resource_path(user.photo_path))
            if os.path.exists(resource_path(f'marks/{update.text}')):
                shutil.rmtree(resource_path(f'marks/{update.text}'))

            db.delete_group(update.text)
            db.delet_group_users(update.text)
            
            await state.clear()
            await update.reply(f"✅ {update.text} guruhi o'chirldi", reply_markup=reply_markup)
        else:
            await state.update_data(confirmed_group = update.text)
            await update.reply(f"⚠️ {update.text} guruhni o'chirmoqchimisiz? Barcha foydalanuvchilar o'chirladi! O'chirish uchun ushbu tugmani qaytdan bosing",
                               reply_markup=groups_markup([group.name for group in db.groups]))
    
    else:
        await state.clear()
        await update.answer("❌ Bunday guruh mavjud emas", reply_markup=reply_markup)


@dp.inline_query()
async def search_users(update: types.InlineQuery, db: DataBase):
    if update.query:
        resolt = [types.InlineQueryResultArticle(title=user.name, 
                                                 id = str(user.id),
                                                 description=f"🆔: {user.id} | {user.group}",
                                                 input_message_content=types.InputTextMessageContent(
                                                     message_text=f"{user.name} \n🆔: {user.id} \nGuruh: {user.group}"
                                                 )) for user in db.search_users(update.query)]
        if resolt:
            await update.answer(resolt, cache_time=1)
        else:
            await update.answer([types.InlineQueryResultArticle(
                id = 'nothing_found',
                title="🤷🏻‍♂️ Birotaham foydalanuvchi topilmadi",
                input_message_content=types.InputTextMessageContent(message_text="🤷🏻‍♂️ Birotaham foydalanuvchi topilmadi")
            )], cache_time=1)
    else:
        resolt = [types.InlineQueryResultArticle(title=user.name, 
                                                 id = str(user.id),
                                                 description=f"🆔: {user.id} | {user.group}",
                                                 input_message_content=types.InputTextMessageContent(
                                                     message_text=f"{user.name} \n🆔: {user.id} \nGuruh: {user.group}"
                                                 )) for user in db.get_last_users()]
        if resolt:
            await update.answer(resolt, cache_time=1)
        else:
            await update.answer([types.InlineQueryResultArticle(
                id = 'nothing_exsit',
                title="🤷🏻‍♂️ Hozirda birortaham foydalanuvchi yo'q",
                input_message_content=types.InputTextMessageContent(message_text="🤷🏻‍♂️ Hozirda birortaham foydalanuvchi yo'q")
            )], cache_time=1)


@dp.message(lambda message: message.from_user.id in ADMINS_ID)
async def main_handler(message: Message, db: DataBase, state: FSMContext) -> None:
    if message.via_bot:
        return

    if message.text == "➕ Qo'shish":
        buttons = AutoButtons(width=3)
        for group in db.groups:
            buttons.add_button(InlineKeyboardButton(text=group.name, callback_data=f'group_{group.name}'))

        buttons.add_button(InlineKeyboardButton(text="➕ Qo'shish", callback_data='add_group'), new_line=True)
        await message.answer("Yangi foydalnuvchi guruhni tanlang 👇", reply_markup=buttons.inline_markup)
    
    elif message.text == "📦 Jadvallar":
        buttons = AutoButtons(width=3)
        for group in db.groups:
            buttons.add_button(InlineKeyboardButton(text=f"📦 {group.name}", callback_data=f'table_{group.name}'))

        buttons.add_button(InlineKeyboardButton(text="➕ Qo'shish", callback_data='add_group'), new_line=True)
        await message.answer("Jadval guruhni tanlang 👇", reply_markup=buttons.inline_markup)

    elif message.text == "➖  O'chirish":
        await state.set_state(MainState.delete_user)
        await message.answer("Foydalanuvchini id raqamini yuboring", reply_markup=back_markup)
    
    elif message.text == "🗑 Guruh o'chirish":
        await state.set_state(MainState.delete_group)
        await message.reply("O'chirmoqchi bo'lgan guruhni tanlang 👇", reply_markup=groups_markup([group.name for group in db.groups]))

    elif message.text == "📋 Foydalanuvchilar":
        await message.reply("Foydaluvchilar ro'yxatini ko'rish uchun pastdagi tugmani bosing 👇", 
                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔍 Foydalanuvchilar", switch_inline_query_current_chat="")]]))
    else:
        await message.answer("Bosh menyu", reply_markup=reply_markup)



async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    db = DataBase(resource_path('data/data.sqlite'), json_path=resource_path('data/last.json'))
    dp["db"] = db
    await dp.start_polling(bot)


if __name__ == "__main__":
    # logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
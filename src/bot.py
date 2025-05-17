import os
from telebot import TeleBot, types
from datetime import datetime, timedelta


BOT_TOKEN = os.getenv('BOT_TOKEN') or "8081832975:AAFCBtxLiT2sxohtgKKVtPfwG7dNFYjIlf"
bot = TeleBot(BOT_TOKEN)

users = {}
user_states = {}


SERVICES = {
    "Техническое обслуживание": [
        "ТО-1 (10 000 км)", 
        "ТО-2 (30 000 км)",
        "ТО-3 (60 000 км)"
    ],
    "Диагностика": [
        "Компьютерная диагностика",
        "Диагностика двигателя",
        "Проверка подвески"
    ],
    "Консультации": [
        "Подбор автомобиля",
        "Онлайн-консультация механика",
        "Оценка состояния авто"
    ],
    "Доп. услуги": [
        "Шиномонтаж",
        "Химчистка салона",
        "Полировка кузова",
        "Установка доп. оборудования"
    ]
}


def main_menu_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Записаться на услугу", "Мои записи", "Изменить данные")
    return keyboard

def services_keyboard():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for service in SERVICES.keys():
        keyboard.add(service)
    keyboard.add("Отмена")
    return keyboard

def subtypes_keyboard(service):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for subtype in SERVICES[service]:
        keyboard.add(subtype)
    keyboard.add("Назад")
    return keyboard

def generate_dates():
    """Генерация списка дат на 7 дней вперёд (только будни)"""
    dates = []
    today = datetime.now()
    for i in range(1, 8):
        date = today + timedelta(days=i)
        if date.weekday() < 5:  # Пн-Пт
            dates.append(date.strftime("%d.%m.%Y"))
    return dates

def time_slots_keyboard(date):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for time in ["09:00", "11:00", "13:00", "15:00", "17:00"]:
        keyboard.add(f"{date} {time}")
    keyboard.add("Назад")
    return keyboard


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    if user_id not in users:
        users[user_id] = {
            "full_name": None,
            "cars": [],
            "appointments": []
        }
        user_states[user_id] = "GET_NAME"
        bot.send_message(user_id, "👋 Добро пожаловать! Введите ваше имя и фамилию:")
    else:
        user_states[user_id] = "MAIN_MENU"
        bot.send_message(user_id, "Главное меню:", reply_markup=main_menu_keyboard())

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id) == "GET_NAME")
def get_name(message):
    user_id = message.chat.id
    users[user_id]["full_name"] = message.text
    user_states[user_id] = "MAIN_MENU"
    bot.send_message(
        user_id,
        f"✅ Данные сохранены, {message.text}!\nВыберите действие:",
        reply_markup=main_menu_keyboard()
    )

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id) == "MAIN_MENU")
def main_menu(message):
    user_id = message.chat.id
    if message.text == "Записаться на услугу":
        user_states[user_id] = "SELECT_SERVICE"
        bot.send_message(
            user_id,
            "Выберите категорию услуги:",
            reply_markup=services_keyboard()
        )
    elif message.text == "Мои записи":
        show_appointments(user_id)
    elif message.text == "Изменить данные":
        user_states[user_id] = "GET_NAME"
        bot.send_message(user_id, "Введите ваше имя и фамилию:")
    else:
        bot.send_message(user_id, "Используйте кнопки меню 👇", reply_markup=main_menu_keyboard())


@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id) == "SELECT_SERVICE")
def select_service(message):
    user_id = message.chat.id
    if message.text == "Отмена":
        user_states[user_id] = "MAIN_MENU"
        bot.send_message(user_id, "Главное меню:", reply_markup=main_menu_keyboard())
    elif message.text in SERVICES:
        users[user_id]["selected_service"] = message.text
        user_states[user_id] = "SELECT_SUBTYPE"
        bot.send_message(
            user_id,
            f"Выберите услугу ({message.text}):",
            reply_markup=subtypes_keyboard(message.text)
        )

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id) == "SELECT_SUBTYPE")
def select_subtype(message):
    user_id = message.chat.id
    if message.text == "Назад":
        user_states[user_id] = "SELECT_SERVICE"
        bot.send_message(
            user_id,
            "Выберите категорию услуги:",
            reply_markup=services_keyboard()
        )
    elif message.text in SERVICES[users[user_id]["selected_service"]]:
        users[user_id]["selected_subtype"] = message.text
        user_states[user_id] = "SELECT_DATE"
        
        
        dates = generate_dates()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for date in dates:
            keyboard.add(date)
        keyboard.add("Назад")
        bot.send_message(
            user_id,
            "Выберите дату:",
            reply_markup=keyboard
        )

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id) == "SELECT_DATE")
def select_date(message):
    user_id = message.chat.id
    if message.text == "Назад":
        user_states[user_id] = "SELECT_SUBTYPE"
        bot.send_message(
            user_id,
            f"Выберите услугу ({users[user_id]['selected_service']}):",
            reply_markup=subtypes_keyboard(users[user_id]["selected_service"])
        )
    else:
        if message.text == "Сегодня":
            date = datetime.now().strftime("%d.%m.%Y")
        elif message.text == "Завтра":
            date = (datetime.now() + timedelta(days=1)).strftime("%d.%m.%Y")
        else:
            date = message.text
        
        users[user_id]["selected_date"] = date
        user_states[user_id] = "SELECT_TIME"
        bot.send_message(
            user_id,
            f"Выберите время для {date}:",
            reply_markup=time_slots_keyboard(date)
        )

@bot.message_handler(func=lambda msg: user_states.get(msg.chat.id) == "SELECT_TIME")
def select_time(message):
    user_id = message.chat.id
    if message.text == "Назад":
        user_states[user_id] = "SELECT_DATE"
        dates = generate_dates()
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for date in dates:
            keyboard.add(date)
        keyboard.add("Назад")
        bot.send_message(user_id, "Выберите дату:", reply_markup=keyboard)
    else:
        date, time = message.text.split()
        users[user_id]["selected_time"] = time
        
        
        users[user_id]["appointments"].append({
            "service": users[user_id]["selected_service"],
            "subtype": users[user_id]["selected_subtype"],
            "date": date,
            "time": time
        })
        
       
        confirm_msg = (
            "✅ Запись оформлена!\n\n"
            f"👤 Клиент: {users[user_id]['full_name']}\n"
            f"🔧 Услуга: {users[user_id]['selected_subtype']}\n"
            f"📅 Дата: {date}\n"
            f"⏰ Время: {time}\n\n"
            "Спасибо за доверие нашему автотехцентру!"
        )
        
        bot.send_message(
            user_id,
            confirm_msg,
            reply_markup=main_menu_keyboard()
        )
        user_states[user_id] = "MAIN_MENU"


def show_appointments(user_id):
    if not users[user_id]["appointments"]:
        bot.send_message(
            user_id,
            "У вас нет активных записей.",
            reply_markup=main_menu_keyboard()
        )
    else:
        appointments_text = "📋 Ваши записи:\n\n"
        for i, app in enumerate(users[user_id]["appointments"], 1):
            appointments_text += (
                f"{i}. {app['service']} - {app['subtype']}\n"
                f"   📅 {app['date']} ⏰ {app['time']}\n\n"
            )
        bot.send_message(
            user_id,
            appointments_text,
            reply_markup=main_menu_keyboard()
        )


if __name__ == "__main__":
    print("🚗 Бот автотехцентра запущен!")
    bot.infinity_polling()
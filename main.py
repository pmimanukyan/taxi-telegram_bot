import my_classes
# python-telegram-bot
import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

TARIFF, FROM, TO, RES = range(4)
data = []  # [class, from, to]


def start(update: Update, context: CallbackContext):
    """Starts the conversation and asks the user to choose a class of taxi."""
    reply_keyboard = [['Economy', 'Comfort', 'ComfortPLUS', 'Business', 'Minivan']]

    update.message.reply_text(
        'Выбери класс такси на котором хочешь поехать:',
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Class?'
        ),
    )
    return TARIFF


def from_(update: Update, context: CallbackContext):
    """Stores the selected class and asks for a route start address."""
    user = update.message.from_user
    data.append(update.message.text)
    logger.info("Tariff of %s: %s", user.first_name, update.message.text)
    if update.message.text == 'Business':
        update.message.reply_text(
            'О, на деловую встречу? 💸️🤵‍\n\n'
            'Откуда тебя забрать, укажи адрес в виде **город, улица, дом**',
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        update.message.reply_text(
            'Отличный выбор! 😍\n\n'
            'Откуда тебя забрать? Укажи адрес в виде **город, улица, дом**',
            reply_markup=ReplyKeyboardRemove(),
        )
    return FROM


def to_(update: Update, context: CallbackContext):
    """Stores the info about route taxi_class(tariff) and asks for a route start."""
    user = update.message.from_user
    logger.info("FROM: %s", update.message.text)
    data.append(update.message.text)
    update.message.reply_text(
        'Куда направимся? Не забудь про формат ввода! 😉',
    )
    return TO


def res(update: Update, context: CallbackContext):
    """Checks data, finds results and ends the conversation."""
    yandextaxi_class_dict = {
        'Economy': 'econom',
        'Comfort': 'business',
        'ComfortPLUS': 'comfortplus',
        'Business': 'vip',
        'Minivan': 'minivan'
    }
    citymobil_class_dict = {
        'Economy': 'Эконом',
        'Comfort': 'Комфорт',
        'ComfortPLUS': 'Комфорт+',
        'Business': 'Бизнес',
        'Minivan': 'Минивэн'
    }

    user = update.message.from_user
    logger.info("TO: %s", update.message.text)
    data.append(update.message.text)

    geocoder = my_classes.YandexGeocoderAPI.create_object()
    yandex_taxi = my_classes.YandexTaxiAPI.create_object()
    citymobil = my_classes.Citymobil(citymobil_class_dict[data[0]], data[1], data[2])

    update.message.reply_text(
        'Теперь проверь данные!\n\n'
    )
    update.message.reply_text(
        f'Класс - {data[0]}.\n'
        f'Адрес начала маршрута - {geocoder.get_correct_address(data[1])}.\n'
        f'Адрес назначения - {geocoder.get_correct_address(data[2])}.\n'
    )
    update.message.reply_text(
        'Если вдруг найдешь неточности в указанном адресе, то тебе наказание пройти это всё заново через команду /start'
        ' и указать более точный адрес (именно по формату ввода!!!)\n'
        'Рассчитываю стоимость поездки, осталось немного подождать ...\n'
    )

    list_ = yandex_taxi.get_price_time_distance(geocoder, yandextaxi_class_dict[data[0]], data[1], data[2])
    yandex_price = str(int(list_[0][:len(list_[0]) - 3])) + 'р'
    time = list_[1]
    distance = list_[2]

    citymobil_price = citymobil.get_price()
    update.message.reply_text(
        f'Время поездки - {time}\n'
        f'Расстояние - {distance}\n\n'
        f'по стоимости:\n'
        f'Яндекс-такси - {yandex_price}\n'
        f'Ситмобил - {citymobil_price}\n'
    )
    # checking for best agregator
    if int(yandex_price[:len(yandex_price) - 1]) <= int(citymobil_price[:len(citymobil_price) - 1]):
        best_agregator = 'Яндекс-такси'
    else:
        best_agregator = 'Ситимобил'

    update.message.reply_text(
        f'Предлагаем воспользоваться услугами {best_agregator}\n\n'
    )
    return ConversationHandler.END


def cancel(update: Update, context: CallbackContext) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Пока дружище! Надеюсь я тебе помог и ты ещё вернешься!', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Creating the Updater with apikey from Botfather
    with open('botfather.txt', 'r') as f:
        apikey = f.read().splitlines()
    updater = Updater(*apikey)
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Adding conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TARIFF: [MessageHandler(Filters.regex('^(Economy|Comfort|ComfortPLUS|Business|Minivan)$'), from_)],
            FROM: [MessageHandler(Filters.text & ~Filters.command, to_)],
            TO: [MessageHandler(Filters.text & ~Filters.command, res)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()

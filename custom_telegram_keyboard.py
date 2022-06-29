import telebot
import logging

# logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def update_saved_info_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
    change_name_btn = telebot.types.KeyboardButton('Change name')
    change_msg_btn = telebot.types.KeyboardButton('Change message')
    save_btn = telebot.types.KeyboardButton('Save')
    cancel_btn = telebot.types.KeyboardButton('Cancel')
    markup.add(change_name_btn, change_msg_btn, save_btn, cancel_btn)
    return markup


def alert_me_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
    on_btn = telebot.types.KeyboardButton('On')
    off_btn = telebot.types.KeyboardButton('Off')
    markup.add(on_btn, off_btn)
    return markup


def reply_new_user_confirm_save():
    markup = telebot.types.ReplyKeyboardMarkup(row_width=2)
    change_name_btn = telebot.types.KeyboardButton('Change name')
    change_msg_btn = telebot.types.KeyboardButton('Change message')
    confirm_btn = telebot.types.KeyboardButton('Confirm')
    markup.add(change_name_btn, change_msg_btn, confirm_btn)
    return markup

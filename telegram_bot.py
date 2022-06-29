import telebot
import logging
import os
import house_unit_lib as lib
import message_lib
import custom_telegram_keyboard
import neighbour_lib
import config
import database
from custom_telegram_keyboard import reply_new_user_confirm_save
from house_unit_lib import check_unit_existed

import user_manager

import threading

MODE = 'dev'


def validate_unit(_tower, _floor, _unit):
    return lib.validate_house_unit(_tower, _floor, _unit)


user_dict = {}
update_user = {}


class User:
    def __init__(self):
        self.user_name = None
        self.user_id = None
        self.user_tower = None
        self.user_floor = None
        self.user_unit = None
        self.user_message = None


def welcome_existed_user(usr_db: dict, _database):
    neighbour_message = m_find_neighbour(_database,
                                         usr_db["tower"],
                                         usr_db["floor"],
                                         usr_db["unit"])

    return neighbour_message


def display_info_db(user_db: dict) -> str:
    """
    Display user data stored in Database
    :param user_db: json retrieved from database
    :return: info
    """
    name = user_db['name']
    unit = '{}-{}-{}'.format(user_db['tower'], user_db['floor'], user_db['unit'])
    message = user_db['message']

    display = 'Your data\n\nName: {}\nUnit Number:{}\nMessage:{}'.format(name, unit, message)
    return display


def search_existed_user(usr_db: dict, _database):
    neighbour_message = m_find_neighbour(_database,
                                         usr_db["tower"],
                                         usr_db["floor"],
                                         usr_db["unit"])

    return neighbour_message


def m_find_neighbour(_database, _tower, _floor, _unit):
    logger.info("Finding neighbour")

    upper_neighbour_floor, lower_neighbour_floor = lib.find_floor_neighbour(_floor)

    upper_neighbour = None
    lower_neighbour = None

    if upper_neighbour_floor is not None:
        upper_neighbour = _database.find_one({"tower": _tower,
                                              "floor": upper_neighbour_floor,
                                              "unit": _unit})

    if lower_neighbour_floor is not None:
        lower_neighbour = _database.find_one({"tower": _tower,
                                              "floor": lower_neighbour_floor,
                                              "unit": _unit})

    upper_msg = '\nUpper floor neighbour.\nName: {}\nMessage:{}'
    lower_msg = '\nLower floor neighbour.\nName: {}\nMessage:{}'

    if upper_neighbour is None and lower_neighbour is None:
        message = '\nYour neighbour record not found. Please visit me later. Anyway, Congratulations for your new home'
        return message

    elif upper_neighbour is None and lower_neighbour is not None:
        lower_message = lower_msg.format(lower_neighbour['name'], lower_neighbour['message'])
        message = '\nYour upper floor neighbour record not found. Please visit me later. Anyway, Congratulations for ' \
                  'your new home'
        message = '{} \n{}'.format(lower_message, message)

    elif lower_neighbour is None and upper_neighbour is not None:
        upper_message = upper_msg.format(upper_neighbour['name'], upper_neighbour['message'])
        message = '\nYour lower floor neighbour record not found. Please visit me later. Anyway, Congratulations ' \
                  'for your new home'
        message = '{} \n{}'.format(upper_message, message)
    else:
        upper_message = upper_msg.format(upper_neighbour['name'], upper_neighbour['message'])
        lower_message = lower_msg.format(lower_neighbour['name'], lower_neighbour['message'])
        message = '{} \n{}'.format(upper_message, lower_message)

    return message


if __name__ == '__main__':
    # server
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 5000))

    # logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    logger = logging.getLogger(__name__)

    logger.info("Setting up Telegram Bot")

    # Setup Bot
    bot = telebot.TeleBot(config.telegram_key)
    dic_user = {}

    logger.info("Setting up Database")
    # Setup DB
    client_db = database.MongoDB(config.pymongo_key)
    client = client_db.db_client
    db = client_db.user_db
    blocked_db = client_db.blocked_user_db

    # ------------ Decorator ---------------------------------------

    def check_user_existed_in_block_list(_id: str):
        status = blocked_db.find_one({"block_id": _id})
        return True if status is not None else False


    def add_user_to_block_list(_id: str, _database):
        existed_user = check_user_existed_in_block_list(_id)

        if existed_user is False:
            blocked_db.insert_one({"block_id": _id})


    def handle_blocked_user(message):
        chat_id = str(message.chat.id)
        chat_username = str(message.from_user.first_name)
        logging.info(chat_username + " - " + chat_id + " --- Handle blocked user")
        try:
            markup = telebot.types.ReplyKeyboardRemove(selective=False)
            inform_msg = message_lib.INFORMED_BLOCK.format(chat_username)
            bot.send_message(message.chat.id, inform_msg, reply_markup=markup)
            return
        except Exception as e:
            logging.info(chat_username + " - " + chat_id + " --- Some error occurred during handling blocked user")
            logging.info(chat_username + " - " + chat_id + " --- Error : {}".format(e))
            bot.reply_to(message, 'Ops, something crash. Would you mind to start again , /start')


    def register_new_user(message):
        """register new user"""
        chat_id = str(message.chat.id)
        chat_username = str(message.from_user.first_name)
        logging.info(chat_username + " - " + chat_id + " --- Prompts User to enter name")
        markup = telebot.types.ReplyKeyboardRemove(selective=False)
        inform = message_lib.INFORM
        bot.send_message(message.chat.id, inform, reply_markup=markup)
        msg = message_lib.WELCOME_NEW_USER
        message = bot.reply_to(message, msg)
        bot.register_next_step_handler(message, process_name)


    def check_user_background(func):
        def inner_wrapper(*args, **kwargs):
            message = kwargs['message']
            user_database = kwargs['user_db']
            blocked_database = kwargs['block_db']
            chat_id = str(message.chat.id)
            chat_username = str(message.from_user.first_name)

            is_usr_blocked = user_manager.check_user_blocked(blocked_database, chat_id)

            # if chat_id != "1482539336":
            #
            #     inform = 'Hey buddy, currently bot undergoing testing process. Please come later , must come okay !'
            #     bot.send_message(int(chat_id), inform)
            #     return

            if is_usr_blocked is True:
                logging.info(chat_username + " - " + chat_id + " --- Check if User is blocked")
                handle_blocked_user(message)
                return

            is_user_exists = user_manager.check_user_registered(user_database, chat_id)

            if is_user_exists is None:
                logging.info(chat_username + " - " + chat_id + " --- Found new user")
                register_new_user(message)
            else:
                func(message)

        return inner_wrapper


    # ----------------- Bot Command ----------------------------------------------

    # /start
    @bot.message_handler(commands=['start'])
    def _welcome_message(message):
        chat_id = str(message.chat.id)
        chat_username = str(message.from_user.first_name)

        logging.info(chat_username + " - " + chat_id + " --- START")
        logging.info(chat_username + " - " + chat_id + " --- CHECK IF EXISTED USER")

        try:
            internal_start_command(message=message, user_db=db, block_db=blocked_db)

        except Exception as e:
            logging.info(chat_username + " - " + chat_id + " --- Welcome Error : {}".format(e))
            bot.send_message(message.chat.id, 'Ops. Something wrong happened.')


    # /help
    @bot.message_handler(commands=['help'])
    def _help(message):
        markup = telebot.types.ReplyKeyboardRemove(selective=False)
        msg = '/search: You can find your neighbour. \
        \n/start: If you\'re new here, you need save your house unit number and leave a message to help ' \
              'your future neighbour find you.\nYou have the option to write anything, i.e phone number/telegram id/' \
              'Facebook id/email so that your neighbour can reach you.'
        bot.send_message(message.chat.id, msg, reply_markup=markup)


    # /update
    @bot.message_handler(commands=['update'])
    def _update(message):
        chat_id = str(message.chat.id)
        chat_username = str(message.from_user.first_name)
        try:
            logging.info(chat_username + " - " + chat_id + " --- UPDATE INFO")
            internal_update_event(message=message, user_db=db, block_db=blocked_db)

        except Exception as err:
            logging.info(chat_username + " - " + chat_id + " --- UPDATE ERROR : {}".format(str(err)))
            bot.reply_to(message, 'Damn it, something wrong happened with update')


    # /search
    @bot.message_handler(commands=['search'])
    def _search_handler(message):
        chat_id = str(message.chat.id)
        chat_username = str(message.from_user.first_name)
        logging.info(chat_username + " - " + chat_id + " --- SEARCH FOR EXISTED USER")

        internal_search_event(message=message, user_db=db, block_db=blocked_db)


    def process_name(message):
        try:
            chat_id = message.chat.id
            name = message.text
            user = User()
            user.user_name = name
            user_dict[chat_id] = user

            if '/' in name:
                wrong_msg = 'Are you sure that you enter correct name? Enter your name again'
                bot.register_next_step_handler(wrong_msg, process_name)
                return

            if 'hi' in name or 'hello' in name or 'neighbour' in name:
                wrong_msg = 'I think this is not your valid name. Sorry, can I have your name again'
                bot.register_next_step_handler(wrong_msg, process_name)
                return

            msg = bot.reply_to(message, 'Enter your unit number. (Example: B-20-02)')
            bot.register_next_step_handler(msg, process_unit)
        except Exception as e:
            logger.warning('Error occurs when save name. Error : {}'.format(e))
            bot.reply_to(message, 'Ops, you suppose enter your name. Shall we start again, enter /start. ')


    def change_name(message):
        chat_id = str(message.chat.id)
        chat_username = str(message.from_user.first_name)
        logging.info(chat_username + " - " + chat_id + " --- NEW USER : CHANGING NAME BEFORE SAVE")
        try:
            current_user = user_dict[message.chat.id]
            current_name = current_user.user_name
            new_name = message.text
            current_user.user_name = new_name
            logging.info(chat_username + " - " + chat_id + " --- NEW USER : CHANGING NAME FROM {} TO {}"
                                                           "".format(current_name, new_name))
            bot.reply_to(message, 'Name changed')

            display = display_user_info(current_user)
            replied_message = bot.send_message(message.chat.id, display, reply_markup=reply_new_user_confirm_save())
            bot.register_next_step_handler(replied_message, handle_save_confirmation)

        except KeyError:
            logging.info(chat_username + " - " + chat_id + " --- NEW USER : ERROR OCCURS DURING CHANGING NAME."
                                                           "NON EXISTS IN INSTANCES")
        except Exception as e:
            pass


    def change_message(message):
        chat_id = str(message.chat.id)
        chat_username = str(message.from_user.first_name)
        logging.info(chat_username + " - " + chat_id + " --- EXIST USER : CHANGING MESSAGE BEFORE SAVE")
        try:
            current_user = user_dict[message.chat.id]
            current_name = current_user.user_name
            new_message = message.text
            current_user.user_message = new_message
            logging.info(chat_username + " - " + chat_id + " --- EXIST USER : CHANGING MESSAGE FROM {} TO {}"
                                                           "".format(current_name, new_message))
            bot.reply_to(message, 'Message updated')
            display = display_user_info(current_user)
            replied_message = bot.send_message(message.chat.id, display, reply_markup=reply_new_user_confirm_save())
            bot.register_next_step_handler(replied_message, handle_save_confirmation)

        except Exception as e:
            pass


    def process_unit(message):
        try:
            chat_id = message.chat.id
            txt = message.text
            logger.info("User unit: {}".format(txt))

            tower = txt.split('-')[0].upper()
            floor = txt.split('-')[1].upper()
            unit = txt.split('-')[2].upper()

            if len(floor) == 1:
                unit = '0{}'.format(floor)

            if len(unit) == 1:
                unit = '0{}'.format(unit)

            status, error_msg = validate_unit(tower, floor, unit)

            if not status:
                msg = bot.reply_to(message, error_msg + '\nEnter your unit number to save. (Example: B-20-02)')
                bot.register_next_step_handler(msg, process_unit)
                return

            tower = lib.format_tower(tower)
            floor = lib.format_floor(floor)
            unit = lib.format_tower(unit)

            user = user_dict[chat_id]
            user.user_id = chat_id
            user.user_tower = tower
            user.user_floor = floor
            user.user_unit = unit

            check_unit_if_existed = check_unit_existed(db, user)

            if check_unit_if_existed is not None:
                inform = message_lib.BLOCKING_ALERT
                block_id = str(chat_id)
                add_user_to_block_list(block_id, blocked_db)
                bot.reply_to(message, inform)
                return

            msg = bot.reply_to(message, 'What do you want to inform your neighbours (Upper and Lower neighbours only)?')
            bot.register_next_step_handler(msg, process_message)
        except Exception as e:
            bot.reply_to(message, 'Ops, I think that wrong text, you suppose enter unit name. Nevermind, '
                                  'let try again. Enter /start')


    def display_user_info(m_usr):
        title = '\nPlease confirm your details'
        name = '\n\nName : {}'.format(m_usr.user_name)
        unit = '\nUnit : {}-{}-{}'.format(m_usr.user_tower, m_usr.user_floor, m_usr.user_unit)
        message = '\nMessage : {}'.format(m_usr.user_message)
        return title + name + unit + message


    def insert_new_data(m_usr):
        db.insert_one({"id": str(m_usr.user_id),
                       "name": m_usr.user_name,
                       "tower": m_usr.user_tower,
                       "floor": m_usr.user_floor,
                       "unit": m_usr.user_unit,
                       "message": m_usr.user_message,
                       "alert_me": True,
                       "alert_upper": True,
                       "alert_lower": True})

        return 'Thank you. Your unit number and message is saved.\n'


    def edit_info(m_usr):
        exist_data = db.find_one({"id": str(m_usr.user_id)})
        bfore_data = exist_data

        exist_data = {
            "$set": {
                "name": m_usr.user_name,
                "message": m_usr.user_message
            }
        }

        db.update_one(bfore_data, exist_data)

        thank_you_msg = 'Thank you. Your details have been updated.\n'
        return thank_you_msg


    def add_new_data(m_id, m_key, m_value):
        exist_data = db.find_one({"id": m_id})
        bfore_data = exist_data

        exist_data = {
            "$set": {
                m_key: m_value,
            }
        }

        db.update_one(bfore_data, exist_data)

        thank_you_msg = 'Thank you. Your details have been updated.\n'
        return thank_you_msg


    def process_message(message):
        try:
            chat_id = message.chat.id
            msg = message.text
            user = user_dict[chat_id]
            user.user_message = msg
            display = display_user_info(user)
            replied_message = bot.send_message(message.chat.id, display, reply_markup=reply_new_user_confirm_save())
            bot.register_next_step_handler(replied_message, handle_save_confirmation)
        except Exception as e:
            logger.info("Error :{}".format(e))
            bot.reply_to(message, 'ops. You suppose leave message for your neighbour. \n'
                                  'For example, hi neighbours, find me in IG telegram group or contact me '
                                  '01x-xxx.\nShall we try again, Enter /start')


    def handle_save_confirmation(message):
        """Receive reply from custom keyboard"""
        try:
            chat_id = message.chat.id
            msg = message.text
            user = user_dict[chat_id]

            if 'Change name' in msg:
                markup = telebot.types.ReplyKeyboardRemove(selective=False)
                msg = bot.reply_to(message, 'Enter your name', reply_markup=markup)
                bot.register_next_step_handler(msg, change_name)
                return

            if 'Change message' in msg:
                markup = telebot.types.ReplyKeyboardRemove(selective=False)
                msg = bot.reply_to(message, 'Enter new message', reply_markup=markup)
                bot.register_next_step_handler(msg, change_message)
                return

            if 'Confirm' in msg:
                markup = telebot.types.ReplyKeyboardRemove(selective=False)
                thank_you_msg = insert_new_data(user)
                bot.reply_to(message, thank_you_msg, reply_markup=markup)

                search_event(message)

                import time
                time.sleep(1)

                threading.Thread(target=scheduler).start()
                # scheduler()

                return

            if 'Save' in msg:
                markup = telebot.types.ReplyKeyboardRemove(selective=False)
                thank_you_msg = insert_new_data(user)
                bot.reply_to(message, thank_you_msg, reply_markup=markup)

                return

            markup = telebot.types.ReplyKeyboardRemove(selective=False)
            bot.reply_to(message, 'I am sorry that something wrong happened, would you mind to start over by enter '
                                  '/start', reply_markup=markup)

        except Exception as e:
            markup = telebot.types.ReplyKeyboardRemove(selective=False)
            logger.info("Error :{}".format(e))
            bot.reply_to(message, 'ops. Something crash :(.\nShall we try again, Enter /start', reply_markup=markup)


    def handle_alert_confirmation(alert_replied_msg):
        """Receive reply from custom keyboard"""
        try:
            chat_id = alert_replied_msg.chat.id
            msg = alert_replied_msg.text

            if 'On' in msg:
                markup = telebot.types.ReplyKeyboardRemove(selective=False)
                add_new_data(alert_replied_msg.chat.id,
                             "alert_neighbour", True)
                msg = bot.reply_to(alert_replied_msg, 'I will notify you if your neighbours joins with me'
                                                      '', reply_markup=markup)
                bot.register_next_step_handler(msg, change_name)
                return

            if 'Off' in msg:
                markup = telebot.types.ReplyKeyboardRemove(selective=False)
                add_new_data(alert_replied_msg.chat.id,
                             "alert_neighbour", False)
                msg = bot.reply_to(alert_replied_msg, 'I wont disturb you :(', reply_markup=markup)
                bot.register_next_step_handler(msg, change_message)
                return

            markup = telebot.types.ReplyKeyboardRemove(selective=False)
            bot.reply_to(alert_replied_msg, 'Unexpected text. Click On/Off button in your keyboard. Enter'
                                            '', reply_markup=markup)

        except Exception as e:
            markup = telebot.types.ReplyKeyboardRemove(selective=False)
            logger.info("Error :{}".format(e))
            bot.reply_to(alert_replied_msg, 'ops. Something broken. Shall we start again,'
                                            ' Enter /start', reply_markup=markup)


    def update_name(message):
        chat_id = message.chat.id
        chat_username = str(message.from_user.first_name)
        try:

            current_user = update_user[str(message.chat.id)]
            current_name = current_user.user_name
            new_name = message.text
            current_user.user_name = new_name
            logging.info(chat_username + " - " + str(chat_id) + " --- Update : CHANGING NAME FROM {} TO {}"
                                                                "".format(current_name, new_name))
            markup = telebot.types.ReplyKeyboardRemove(selective=False)
            bot.reply_to(message, 'Name updated', reply_markup=markup)
            display = display_user_info(current_user)
            replied_message = bot.send_message(message.chat.id, display,
                                               reply_markup=custom_telegram_keyboard.update_saved_info_keyboard())
            bot.register_next_step_handler(replied_message, handle_update_confirmation)
        except Exception as e:
            markup = telebot.types.ReplyKeyboardRemove(selective=False)
            bot.reply_to(message, 'ops.\nShall we try again, Enter /update', reply_markup=markup)

            chat_id = str(message.chat.id)
            chat_username = str(message.from_user.first_name)
            logging.info(chat_username + " - " + chat_id + " --- UPDATE : ERROR CHANGING NAME BEFORE SAVE")


    def update_message(message):
        chat_id = message.chat.id
        chat_username = str(message.from_user.first_name)
        try:

            current_user = update_user[str(message.chat.id)]
            current_user.user_message = message.text
            logging.info(chat_username + " - " + str(chat_id) + " --- Update : UPDATING MESSAGE")
            markup = telebot.types.ReplyKeyboardRemove(selective=False)
            bot.reply_to(message, 'Message updated', reply_markup=markup)
            display = display_user_info(current_user)
            replied_message = bot.send_message(message.chat.id, display,
                                               reply_markup=custom_telegram_keyboard.update_saved_info_keyboard())
            bot.register_next_step_handler(replied_message, handle_update_confirmation)
        except Exception as e:
            markup = telebot.types.ReplyKeyboardRemove(selective=False)
            bot.reply_to(message, 'ops.\nShall we try again, Enter /update', reply_markup=markup)

            chat_id = str(message.chat.id)
            chat_username = str(message.from_user.first_name)
            logging.info(chat_username + " - " + chat_id + " --- UPDATE : ERROR CHANGING Message BEFORE SAVE")


    def handle_update_confirmation(message):
        """Receive reply from custom keyboard"""
        try:
            chat_id = message.chat.id
            msg = message.text

            if 'Change name' in msg:
                markup = telebot.types.ReplyKeyboardRemove(selective=False)
                msg = bot.reply_to(message, 'Enter new name', reply_markup=markup)
                bot.register_next_step_handler(msg, update_name)
                return

            if 'Change message' in msg:
                markup = telebot.types.ReplyKeyboardRemove(selective=False)
                msg = bot.reply_to(message, 'Enter new message', reply_markup=markup)
                bot.register_next_step_handler(msg, update_message)
                return

            if 'Save' in msg:
                markup = telebot.types.ReplyKeyboardRemove(selective=False)
                user = update_user[str(chat_id)]
                thank_you_msg = edit_info(user)
                bot.reply_to(message, thank_you_msg, reply_markup=markup)
                return

            if 'Cancel' in msg:
                markup = telebot.types.ReplyKeyboardRemove(selective=False)
                update_user.pop(str(chat_id))
                thank_you_msg = 'Ok' \
                                ''
                bot.reply_to(message, thank_you_msg, reply_markup=markup)
                return

            markup = telebot.types.ReplyKeyboardRemove(selective=False)
            bot.reply_to(message, 'I am sorry that something wrong happened, would you mind to start over by enter '
                                  '/update', reply_markup=markup)

        except Exception as e:
            markup = telebot.types.ReplyKeyboardRemove(selective=False)
            logger.info("Error :{}".format(e))
            bot.reply_to(message, 'I am sorry that something wrong happened, would you mind to start over by enter '
                                  '/update', reply_markup=markup)


    # non-command message
    @bot.message_handler(func=lambda m: True)
    def chat(message):
        txt = message.text
        if any(x in txt.lower() for x in ["thank", "thx", "cool"]):
            msg = "anytime"
            bot.send_message(message.chat.id, msg)
        elif any(x in txt.lower() for x in ["love you"]):
            msg = "Sorry, I have a beautiful girlfriend."
            bot.send_message(message.chat.id, msg)
        elif any(x in txt.lower() for x in ["handsome"]):
            msg = "Thank you <3"
            bot.send_message(message.chat.id, msg)


    # ------------------------- Internal Logic ----------------------------------------
    @check_user_background
    def internal_start_command(message):
        logger.info('Internal start command function is called when start enter')
        search_event(message)


    @check_user_background
    def internal_search_event(message):
        search_event(message)


    @check_user_background
    def internal_update_event(message):
        chat_id = str(message.chat.id)
        chat_username = str(message.from_user.first_name)
        check_user_existed = user_manager.check_user_registered(db, chat_id)

        logging.info(chat_username + " - " + chat_id + " --- UPDATE INFO : Existed User")
        need_update_user = User()
        need_update_user.user_name = check_user_existed["name"]
        need_update_user.user_id = check_user_existed["id"]
        need_update_user.user_tower = check_user_existed["tower"]
        need_update_user.user_floor = check_user_existed["floor"]
        need_update_user.user_unit = check_user_existed["unit"]
        need_update_user.user_message = check_user_existed["message"]
        update_user[chat_id] = need_update_user
        info = display_user_info(need_update_user)
        msg = bot.reply_to(message, info, reply_markup=custom_telegram_keyboard.update_saved_info_keyboard())
        bot.register_next_step_handler(msg, handle_update_confirmation)


    def search_event(message):
        chat_id = str(message.chat.id)
        chat_username = str(message.from_user.first_name)
        logging.info(chat_username + " - " + chat_id + " --- SEARCH FOR EXISTED USER")
        check_user_existed = user_manager.check_user_registered(db, chat_id)
        markup = telebot.types.ReplyKeyboardRemove(selective=False)
        result = "{},\n{}".format(chat_username, search_existed_user(check_user_existed, db))
        bot.send_message(message.chat.id, result, reply_markup=markup)


    def scheduler(skip_this_user=None):
        # Setup DB
        scd_client_db = database.MongoDB(config.pymongo_key)
        # client = scd_client_db.db_client
        scd_db = scd_client_db.user_db
        all_users = scd_db.distinct(key='id')

        logging.info('Start notify')

        for user in all_users:

            if skip_this_user is not None:
                if user == skip_this_user:
                    logging.info('Skipping this user --- {} -----'.format(user))
                    continue

            msg = neighbour_lib.handle_notify_user_floor_neighbour(scd_db, user)

            if msg is None:
                logging.info('Skipping notifying --- {} -----'.format(user))
                continue

            logging.info('Notifying --- {} -----'.format(user))

            receiver_id = int(user)

            bot.send_message(receiver_id, '[NOTIFICATION]\n' + msg)

        return


    # To be implemented feature
    # @check_user_background
    # def alert_command(alert_chat_message):
    #     alert_chat_id = str(alert_chat_message.chat.id)
    #     alert_chat_username = str(alert_chat_message.from_user.first_name)
    #
    #     logging.info(alert_chat_username + " - " + alert_chat_id + " --- ALERT BUSINESS LOGIC")
    #
    #     prompts_user = 'Turn on notification when upper and lower neighbours joins IG_Neighbour_Finder'
    #     keyboard_markup = custom_telegram_keyboard.alert_me_keyboard()
    #     replied_output = bot.reply_to(alert_chat_message, prompts_user, reply_markup=keyboard_markup)

    # ------------------------------------------------------------------------------------

    if MODE == 'dev':
        # import threading

        # threading.Thread(target=scheduler).start()
        bot.infinity_polling(True)

    elif MODE == 'prod':
        import flask

        server = flask.Flask(__name__)

        telegrambotkey = config.telegram_key

        @server.route('/{}'.format(telegrambotkey), methods=['POST'])
        def getMessage():
            bot.process_new_updates([telebot.types.Update.de_json(
                flask.request.stream.read().decode("utf-8"))])
            return "!", 200


        @server.route("/")
        def webhook():
            bot.remove_webhook()
            bot.set_webhook(url='https://botfindneighbour.herokuapp.com/{}'.format(telegrambotkey))
            return "!", 200

        threading.Thread(target=scheduler).start()
        server.run(host=host, port=port)

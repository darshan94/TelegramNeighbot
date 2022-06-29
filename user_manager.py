from telegram_bot import MODE


def is_user_blocked(_id: str, db):
    status = db.find_one({"block_id": _id})
    return True if status is not None else False


def do_if_user_blocked():
    pass


def do_if_user_new():
    pass


def do_if_user_exist():
    pass


def check_if_admin(func):
    def inner(*args, **kwargs):
        usr = func(*args, **kwargs)

        if usr is not None and MODE == 'dev':
            if usr["id"] == "1482539336":
                usr = None
        return usr

    return inner


def check_user_registered(_database, _chat_id: str):
    user_registered = _database.find_one({"id": _chat_id})
    return user_registered


def check_user_blocked(_database, _chat_id: str):
    status = _database.find_one({"block_id": _chat_id})
    return True if status is not None else False

"""
Class to handle with cloud database
"""
import pymongo
import config


class MongoDB(object):
    def __init__(self, key):
        self.db_client = pymongo.MongoClient(key)
        db_name = "Telegram_IGNeighbours"
        user_collection = "users"
        test_data = "usrs_testing"
        blocked_user_collection = "block_users"
        self.user_db = self.db_client[db_name][user_collection]
        self.blocked_user_db = self.db_client[db_name][blocked_user_collection]

    def insert_new(self):
        pass

    def find_one(self, db):
        pass

    def replace_one(self):
        pass

    def add_attribute(self):
        pass


def add_attribute(_database):
    all_user = _database.distinct(key="id")

    for user in all_user:
        exist_data = _database.find_one({"id": user})
        bfore_data = exist_data

        exist_data = {
            "$set": {
                "alert_me": True,
                "alert_upper": True,
                "alert_lower": True
            }
        }

        _database.update_one(bfore_data, exist_data)


def set_attribute(_database, _id, _key, _value):
    exist_data = _database.find_one({"id": _id})
    bfore_data = exist_data

    exist_data = {
        "$set": {
            _key: _value
        }
    }

    _database.update_one(bfore_data, exist_data)


if __name__ == '__main__':

    client_db = MongoDB(config.pymongo_key)
    client = client_db.db_client
    db = client_db.user_db

    # add_attribute(db)
    db.update_many({}, {"$set": {
                "alert_me": True,
                "alert_upper": True,
                "alert_lower": True}})

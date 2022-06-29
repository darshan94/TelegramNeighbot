import logging
import house_unit_lib as lib
import database

# logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def display_message(_title, _data):
    return '{}\n\nName: {}\nUnit: {}-{}-{}\nMessage:{}'.format(_title,
                                                               _data["name"],
                                                               _data["tower"],
                                                               _data["floor"],
                                                               _data["unit"],
                                                               _data["message"])


def find_neighbour(_database, _tower, _neighbour_floor, _unit):
    return _database.find_one({"tower": _tower,
                               "floor": _neighbour_floor,
                               "unit": _unit})


def search_floor_neighbour(_floor_type, user_data, _database):
    logger.info("Searching floor neighbour")


    _tower = user_data["tower"]
    _floor = user_data["floor"]
    _unit = user_data["unit"]

    neighbour_floor = None

    if _floor_type == 'upper':
        neighbour_floor, _ = lib.find_floor_neighbour(_floor)

    elif _floor_type == 'lower':
        _, neighbour_floor = lib.find_floor_neighbour(_floor)

    neighbour = find_neighbour(_database, _tower, neighbour_floor, _unit)

    return neighbour


def notify_user_floor_neighbour(_database, _id: str):
    usr = _database.find_one({"id": _id})

    if usr["alert_me"] is False:
        logger.info("Skipping notify for user don't to be notified")
        return None

    no_neighbour = False

    upper_neigh_notifications = ''
    lower_neigh_notifications = ''

    if usr["alert_upper"] is True:
        upper_neighbour = search_floor_neighbour(_floor_type='upper', user_data=usr, _database=_database)

        if upper_neighbour is None:
            pass
        else:
            upper_neigh_notifications = display_message(_title='Upper floor neighbour', _data=upper_neighbour)
            database.set_attribute(_database, _id, _key="alert_upper", _value=False)
            no_neighbour = True

    if usr["alert_lower"] is True:
        lower_neighbour = search_floor_neighbour(_floor_type='lower', user_data=usr, _database=_database)

        if lower_neighbour is None:
            pass
        else:
            lower_neigh_notifications = display_message(_title='Lower floor neighbour', _data=lower_neighbour)
            database.set_attribute(_database, _id, _key="alert_lower", _value=False)
            no_neighbour = True

    return upper_neigh_notifications, lower_neigh_notifications, no_neighbour


def handle_notify_user_floor_neighbour(_database, _id):
    """
    Modify returned message based on the existence of the neighbours
    :param _database: MongoDB data
    :param _id: telegram user id
    :return:
    """
    data = notify_user_floor_neighbour(_database, _id)
    if data is None:
        raise Exception('No neighbour')
    found_neighbour_1, found_neighbour_2, found_neighbour = data[0], data[1], data[2]

    if found_neighbour is True:
        header_msg = 'Hey buddy, I found your neighbour.\n\n{}\n\n\n{}'.format(found_neighbour_1, found_neighbour_2)
    else:
        # header_msg = 'My bad, I do not have any records of your neighbours. Anyway, I will notify you once they ' \
        #              'joins here.'
        return None

    return header_msg

# Find my neighbour library
import logging

floor = ('09', '10', '11', '12', '13', '13A', '15',
         '16', '17', '18', '19', '20', '21', '22',
         '23', '23A', '25', '26', '27', '28', '29',
         '30', '31', '32', '33', '33A', '35', '36',
         '37', '38', '39', '40', '41', '42', '43', '43A', '45')

UNITS = ('01', '02', '03', '3A', '05', '06', '6', '07', '08', '09', '10', '11', '12', '13')

SPECIAL_FLOOR = ('13a', '23a', '33a', '43a')
SPECIAL_UNIT = '3a'
TOWER_A_SPECIAL_UNITS = ('05', '5', '06', '6', '07', '7', '08', '8', '09', '9', '10', '11', '12', '13')
TOWER_B_SPECIAL_UNITS = ('08', '8', '09', '9', '10', '11', '12', '13')

# logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_house_unit(_tower, _floor, _unit):
    logger.info('Validating provided house unit')
    logger.info('Validating provided house tower')
    valid = validate_tower(_tower)

    if valid is not True:
        error_message = 'Invalid Unit No'
        logger.info(error_message)
        print("Not valid Unit")
        return False, "Wrong Tower"

    logger.info('Validating provided house flor')

    valid = validate_floor(_floor)

    if valid is not True:
        error_message = 'Invalid Unit No'
        logger.info(error_message)
        print("Not valid Unit")
        return False, "Wrong Floor Number"

    valid = validate_unit(_unit)

    if valid is not True:
        error_message = 'Invalid Unit No'
        logger.info(error_message)
        print("Not valid Unit")
        return False, "Wrong Unit Number"

    print("Provided unit is valid")

    valid, msg = validate_special_unit(_tower, _floor, _unit)
    if valid is True:
        print("This is special unit. Not for residential purpose")
        return False, msg

    return True, None


def validate_tower(_tower):
    """Validate tower"""
    if _tower.upper() == 'A' or _tower.upper() == 'B':
        logger.info("valid tower")
        return True
    else:
        logger.info("Invalid tower")
        return False


def validate_floor(_floor):
    """validate floor"""
    if 'a' in _floor:
        _floor = _floor.upper()

    if _floor in floor:
        logger.info("valid floor")
        return True
    else:
        logger.info("Invalid floor")
        return False


def validate_unit(_unit):
    """validate unit"""
    if 'a' in _unit:
        _unit = _unit.upper()

    if _unit in UNITS:
        logger.info("valid unit number")
        return True
    else:
        logger.info("Invalid unit number")
        return False


def validate_special_unit(_tower, _floor, _unit):
    if _tower.upper() == 'A':
        if (_floor == '30' or _floor == '29') and _unit in TOWER_A_SPECIAL_UNITS:
            msg = 'Wrong Unit No. Provided unit is not for residential purpose'
            logger.info(msg)
            print(msg)
            return True, msg

    if _tower.upper() == 'B':
        if (_floor == '30' or _floor == '29') and _unit in TOWER_B_SPECIAL_UNITS:
            msg = 'Wrong Unit No. Provided unit is not for residential purpose'
            logger.info(msg)
            print(msg)
            return True, msg
    return False, None


def find_floor_neighbour(_floor):
    # check floor is not 8th
    # check floor is not 46th
    find_upper = True
    find_lower = True

    if _floor == '45':
        print('Current Unit is in top floor. Cannot have upper floor neighbour')
        find_upper = False
    if _floor == '9':
        print('Current Unit is in bottom floor. Cannot have lower floor neighbour')
        find_lower = False

    upper_floor_neighbour = None
    lower_floor_neighbour = None
    if find_upper is True:
        for index, value in enumerate(floor):
            if value == _floor:
                upper_floor_neighbour = floor[index + 1]
                logger.info("Found upper floor neighbour")
                break

    if find_lower is True:
        for index, value in enumerate(floor):
            if value == _floor:
                lower_floor_neighbour = floor[index - 1]
                logger.info("Found lower floor neighbour")
                break

    return upper_floor_neighbour, lower_floor_neighbour


def format_tower(tower):
    """convert lower case to upper character"""
    return tower.upper()


def format_floor(m_floor):
    """convert lower case to upper character"""
    if 'a' in m_floor:
        m_floor = m_floor.replace('a', 'A')

    single_digit = ['1', '2', '3', '5', '6', '7', '8', '9']

    if m_floor in single_digit:
        m_floor = '0{}'.format(m_floor)

    return m_floor


def format_unit(m_unit):
    """convert lower case to upper character"""
    if 'a' in m_unit:
        m_unit = m_unit.replace('a', 'A')

    single_digit = ['1', '2', '3', '5', '6', '7', '8', '9']

    if m_unit in single_digit:
        m_unit = '0{}'.format(m_unit)

    return m_unit


def check_unit_existed(_database, user_obj) -> dict:
    check_unit_already_registered = _database.find_one({"tower": user_obj.user_tower,
                                                        "floor": user_obj.user_floor,
                                                        "unit": user_obj.user_unit})
    return check_unit_already_registered
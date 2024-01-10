import re

from sapphire_backend.imomo.errors import LexiconError

# Compiled regular expressions used in the lexicon methods
_USERNAME = re.compile(r"^\w{6,24}$")
_DIGIT = re.compile(r"\d")
_EMAIL = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,4}$", flags=re.IGNORECASE)
_VARLENGTH_ALPHANUMERIC = lambda length: re.compile(r"^[\w\s-]{1,%d}$" % length, flags=re.UNICODE)
_FULL_NAME = _VARLENGTH_ALPHANUMERIC(256)
_ORGANIZATION = _VARLENGTH_ALPHANUMERIC(100)
_HYDROLOGICAL_STATION_ID = re.compile(r"^\d{1,100}$", flags=re.UNICODE)
_RIVER_BASIN = _VARLENGTH_ALPHANUMERIC(100)
_COUNTRY_CODE_ALPHA_2 = re.compile(r"^[A-Z]{2}$")

MIN_PASSWORD_LENGTH = 6
MAX_PASSWORD_LENGTH = 72


def username(value):
    """Username syntax validator.

    Raises:
        LexiconError: If the username fails validation, i.e. the username is
        not a string between 6 and 24 characters, containing only
        alphanumerical characters and/or underscore.

    Returns:
        The username in lowercase.
    """
    if _USERNAME.match(value) is None:
        raise LexiconError(
            "Username must contain only letters and numbers, " "and be between 6 and 24 characters long."
        )
    return value.lower()


def password(value):
    """Password rules validator.

    Raises:
        LexiconError: If the password fails validation, i.e. it is shorter than
        6  characters, contains at least one uppercase letter and
        one number. Special characters are allowed.
    Returns:
        The input value unmodified.
    """
    if len(value) < MIN_PASSWORD_LENGTH or len(value) > MAX_PASSWORD_LENGTH:
        raise LexiconError("Password must be between 6 and 72 characters.")
    if value.islower():
        raise LexiconError("Password must contain at " "least one uppercase letter.")
    if _DIGIT.search(value) is None:
        raise LexiconError("Password must contain at least one digit.")
    return value


def email(value):
    """Email syntax validator.

    Raises:
        LexiconError: If the e-mail fails validation according to the basic
        regex for emails taken from:
        http://www.regular-expressions.info/email.html
        Or if the email is longer than 100 characters.
    Returns:
        The input value in lowercase.
    """
    if _EMAIL.match(value) is None or len(value) > 100:
        raise LexiconError("Input is not a valid e-mail address or exceeds " "the 100 character limit.")
    return value.lower()


def full_name(value):
    """Full name syntax validator.

    Raises:
        LexiconError: If the full name given contains any non-alphanumerical
        characters or whitespaces, or if its length is greater than 256
        characters.
    Returns:
        The input value with trailing whitespaces removed.
    """
    clean_input = value.strip()
    if _FULL_NAME.match(clean_input) is None:
        raise LexiconError(
            "Full name can only contain alphanumerical " "characters and have a max length of " "256 characters."
        )
    return clean_input


def organization_name(value):
    """Organization syntax validator.

    Raises:
        LexiconError: If the organization contains any non-alphanumerical
        characters or whitespaces, of if its length is greater than 100.
    Returns:
        The input value with trailing whitespaces removed.
    """
    clean_input = value.strip()
    if _ORGANIZATION.match(clean_input) is None:
        raise LexiconError(
            "Organization names can only contain "
            "alphanumerical characters and have a max length "
            "of 100 characters."
        )
    return clean_input


def hydrological_station_id(value):
    """Hydrological station id syntax validator.

    Raises:
        LexiconError: If the station id contains non-numerical characters
            and/or is greater than 50 characters in length.
    Returns:
        A string version if the input value, in case the id was passed as an
        integer.
    """
    str_value = str(value)
    if _HYDROLOGICAL_STATION_ID.match(str_value) is None:
        raise LexiconError(
            "Hydrological station IDs can only contain digits " "and be between 1 and 100 characters in length."
        )
    return str_value


def river_basin(value):
    """River or basin syntax validator.

    Raises:
        LexiconError: If the input value is not an alphanumerical string with
            spaces or if its length is greater than 100 characters.
    Returns:
        The unmodified input value.
    """
    if _RIVER_BASIN.match(value) is None:
        raise LexiconError("River and Basin names must be alphanumerical " "strings with no more than 100 characters.")
    return value


def country_code(value):
    """Country code syntax validator.

    Raises:
        LexiconError: If the input value does not match an Alpha-2 country
            code.
    Returns:
        The input value in uppercase.
    """
    uppercased = value.upper()
    if _COUNTRY_CODE_ALPHA_2.match(uppercased) is None:
        raise LexiconError("Input value does not match an Alpha-2 country " "code.")
    return uppercased


def latitude(value):
    """Latitude syntax validator.

    Raises:
        LexiconError: If the input value can not be parsed to a float or
            is outside of the valid range for latitude.
    Returns:
        Float value parsed from the input.
    """
    try:
        float_value = float(value)
    except ValueError:
        raise LexiconError("Latitude must be a floating point number.")
    if abs(float_value) > 90:
        raise LexiconError("Valid latitude values are between -90 and 90.")
    return float_value


def longitude(value):
    """Longitude syntax validator.

    Raises:
        LexiconError: If the input value can not be parsed to a float or
            is outside of the valid range for longitude.
    Returns:
        Float value parsed from the input.
    """
    try:
        float_value = float(value)
    except ValueError:
        raise LexiconError("longitude must be a floating point number.")
    if abs(float_value) > 180:
        raise LexiconError("Valid longitude values are between -180 and 180.")
    return float_value

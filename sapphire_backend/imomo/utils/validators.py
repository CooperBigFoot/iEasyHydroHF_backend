
import operator
import six
import base64
# import pytz
from zoneinfo import ZoneInfo
import datetime
from dateutil import parser
from distutils.util import strtobool

import sapphire_backend.imomo.errors as errors
from sapphire_backend.imomo.utils.strings import snake_to_camel, camel_to_snake


def get_json_parameter(json, key, *args, **kwargs):

    if args:
        default = args[0]
        raise_exception = False
    else:
        default = None
        raise_exception = True

    camel_case = kwargs.get('camel_case', True)
    validator = kwargs.get('validator', None)

    key = snake_to_camel(key) if camel_case else key

    try:
        value = json[key]
        if validator:
            value = validator(value, key)
    except KeyError:
        if raise_exception:
            raise errors.ValidationError("Missing '{}' parameter.".format(key))
        else:
            value = default

    return value


def int_validator(value, key_name):
    try:
        return int(value)
    except (ValueError, TypeError):
        raise errors.ValidationError("Invalid '{}' parameter type. Expected integer value.".format(key_name))


def int_or_none_validator(value, key_name):
    if value is not None:
        try:
            return int(value)
        except (ValueError, TypeError):
            raise errors.ValidationError(
                "Invalid '{}' parameter type. Expected None or integer value.".format(key_name))


def float_validator(value, key_name):
    try:
        return float(value)
    except (ValueError, TypeError):
        raise errors.ValidationError(
            "Invalid '{}' parameter type. Expected float value.".format(key_name))


def float_or_none_validator(value, key_name):
    if value is not None:
        try:
            return float(value)
        except (ValueError, TypeError):
            raise errors.ValidationError(
                "Invalid '{}' parameter type. Expected None or float value.".format(key_name))


def date_validator(date, key_name='date'):
    try:
        date = float(date)
    except (ValueError, AttributeError):
        pass
    else:
        try:
            return datetime.datetime.utcfromtimestamp(date)
        except ValueError:
            raise errors.ValidationError("Invalid timestamp for '{}' parameter.".format(key_name))

    try:
        return parser.parse(date)
    except (ValueError, TypeError):
        raise errors.ValidationError("Invalid date string for '{}' parameter.".format(key_name))


def date_or_none_validator(date, key_name='date'):
    if date is not None:
        return date_validator(date, key_name)

    return None


def positive_float_validator(value, key_name):
    value = float_validator(value, key_name)
    if value < 0:
        raise errors.ValidationError(
            'Parameter "{key_name}" should be a positive number')

    return value


def list_validator(value, key_name):
    if not isinstance(value, list):
        raise errors.ValidationError('Parameter "{}" should be list.'.format(
            key_name
        ))

    return value


def str_bool_validator(value, key_name):
    if value is None:
        return False

    if isinstance(value, bool):
        return value

    try:
        return strtobool(value)
    except (ValueError, AttributeError):
        raise errors.ValidationError('Invalid bool value for {}'.format(key_name))


def range_validator(
        key,
        value,
        minimum,
        maximum,
        minimum_method='ge',
        maximum_method='le'
):
    min_method_choices = {
        'gt': '<',
        'ge': '[',
    }
    max_method_choices = {
        'lt': '>',
        'le': ']',
    }
    if minimum_method not in min_method_choices:
        raise AttributeError(
            'Invalid minimum method. Valid choices are "{}"'.format(
                '", "'.join(min_method_choices)
            ))

    if maximum_method not in max_method_choices.keys():
        raise AttributeError(
            'Invalid maximum method. Valid choices are "{}"'.format(
                '", "'.join(max_method_choices)
            ))

    minimum_method_ = getattr(operator, minimum_method)
    maximum_method_ = getattr(operator, maximum_method)

    if not (minimum_method_(value, minimum)
            and maximum_method_(value, maximum)):
        raise errors.ValidationError(
            'Invalid value ({value}) for "{key}" parameter. Valid range is '
            '{min_bracket}{min_value}, {max_value}{max_bracket}'.format(
                value=value,
                key=key,
                min_bracket=min_method_choices[minimum_method],
                max_bracket=max_method_choices[maximum_method],
                min_value=minimum,
                max_value=maximum,
            ))

    return value


def ordering_param(query_param, valid_fields, key_name='order_by', to_snake=True):
    if query_param is None:
        return None, None

    if query_param.startswith('-'):
        ordering = 'desc'
        field = query_param[1:]
    else:
        ordering = 'asc'
        field = query_param

    if to_snake:
        field = camel_to_snake(field)

    if field not in valid_fields:
        raise errors.ValidationError(
            'Invalid "{key_name}" parameter value: {query_param}.'.format(
                key_name=key_name,
                query_param=query_param,
            ))

    return field, ordering


def base64_decode_validator(base64str, key_name):
    if isinstance(base64str, six.string_types):
        # Check if the base64 string is in the "data:" format
        if 'data:' in base64str and ';base64,' in base64str:
            # Break out the header from the base64 content
            header, base64str = base64str.split(';base64,')

        try:
            return base64.b64decode(base64str)
        except TypeError as ex:
            raise errors.ValidationError(
                'Invalid "base64" file string for "{key}" '
                'parameter. Details: {ex}'.format(
                    key=key_name,
                    ex=ex,
                ))

    raise errors.ValidationError(
        'Parameter "{key_name}" should be a base64 string.'.format(
            key_name=key_name
        ))


def timezone_validator(timezone, key_name='timezone'):
    try:
        ZoneInfo(timezone)
        # pytz.timezone(timezone)
    except (AttributeError, pytz.UnknownTimeZoneError):
        raise errors.ValidationError(
            'Invalid timezone "{}" for "{}" parameter.'.format(
                timezone, key_name
            ))

    return timezone


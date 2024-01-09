# -*- encoding: UTF-8 -*-
import re
import string


def camel_to_snake(s):
    """Utility to convert from a string in camelCase to snake_case.

    As seen in:
        http://stackoverflow.com/a/1176023/895956

    Note that this does not create underscores for white spaces.

    Args:
        s: camelCase string to convert.
    """
    first_cap_re = re.compile('(.)([A-Z][a-z]+)')
    all_cap_re = re.compile('([a-z0-9])([A-Z])')

    s1 = first_cap_re.sub(r'\1_\2', s)
    s2 = all_cap_re.sub(r'\1_\2', s1)
    return s2.lower()


def snake_to_camel(s):
    """Utility to convert from a string in snake_case to camelCase.

    Args:
        s: snake_case string to convert.
    """
    return s[0].lower() + string.capwords(s, '_').replace('_', '')[1:]


def camel_to_snake_json(obj):
    """Converts all the keys in a JSON object from camelCase to snake_case.

    Args:
        obj: The python representation of a JSON object, it can be
             dict, list, str, int or float.
    """
    if isinstance(obj, dict):
        return {camel_to_snake(k): camel_to_snake_json(v)
                for k, v in obj.items()}
    elif isinstance(obj, list):
        return [camel_to_snake_json(elem) for elem in obj]
    else:
        return obj


def to_unicode(str_or_unicode):
    if isinstance(str_or_unicode, str):
        return str_or_unicode.decode('utf-8')

    return str_or_unicode


def to_str(str_or_unicode):
    if isinstance(str_or_unicode, unicode):
        return str_or_unicode.encode('utf-8')

    return str_or_unicode
